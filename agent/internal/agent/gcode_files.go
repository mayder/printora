package agent

import (
	"context"
	"net/url"
	"path"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

const gcodeFilesCacheTTL = 20 * time.Second
const maxGcodeFilesListLimit = 100
const defaultGcodeFilesListLimit = 50
const maxGcodeFileThumbnailRequests = 24
const gcodeFileEnrichmentConcurrency = 4

type gcodeFilesListCache struct {
	mu        sync.Mutex
	expiresAt time.Time
	key       string
	payload   map[string]any
}

func (c *MoonrakerClient) GcodeFiles(ctx context.Context, jobPayload map[string]any) map[string]any {
	limit := intFromAny(jobPayload["limit"])
	if limit <= 0 || limit > maxGcodeFilesListLimit {
		limit = defaultGcodeFilesListLimit
	}
	offset := intFromAny(jobPayload["offset"])
	if offset < 0 {
		offset = 0
	}
	directory := normalizedMoonrakerDirectoryPath(stringValue(jobPayload["directory"]))
	query := strings.ToLower(strings.TrimSpace(stringValue(jobPayload["query"])))
	sortKey := normalizedGcodeFileSortKey(stringValue(jobPayload["sort"]))
	sortDirection := normalizedGcodeFileSortDirection(stringValue(jobPayload["direction"]))
	refresh := boolFromAny(jobPayload["refresh"])
	includeMetadata := boolFromAny(jobPayload["include_metadata"])
	includeThumbnails := boolFromAny(jobPayload["include_thumbnails"])
	if includeMetadata == false && jobPayload["include_metadata"] == nil {
		includeMetadata = true
	}
	if includeThumbnails == false && jobPayload["include_thumbnails"] == nil {
		includeThumbnails = true
	}
	cacheKey := strings.Join([]string{
		intString(limit),
		intString(offset),
		directory,
		query,
		sortKey,
		sortDirection,
		strconv.FormatBool(includeMetadata),
		strconv.FormatBool(includeThumbnails),
	}, "\x00")
	if !refresh {
		if cached := c.gcodeFiles.get(cacheKey); cached != nil {
			cached["cache_state"] = "hit"
			return cached
		}
	}

	payload := map[string]any{
		"safe_mode":         "read_only",
		"kind":              "gcode_files",
		"root":              "gcodes",
		"data_state":        "live",
		"cache_state":       "miss",
		"cache_ttl_seconds": int(gcodeFilesCacheTTL.Seconds()),
		"fetched_at":        time.Now().UTC().Format(time.RFC3339),
		"offset":            offset,
		"limit":             limit,
		"directory":         directory,
		"query":             query,
		"sort":              sortKey,
		"direction":         sortDirection,
	}
	listPayload := map[string]any{}
	if err := c.get(ctx, "/server/files/list?root=gcodes", "gcode_files", listPayload); err != nil {
		payload["data_state"] = "error"
		payload["error"] = err.Error()
		payload["summary"] = "Moonraker não retornou a lista de G-code."
		return payload
	}

	allFiles := normalizeGcodeFileList(listPayload["gcode_files"])
	filtered := filterGcodeFiles(allFiles, directory, query)
	sortGcodeFiles(filtered, sortKey, sortDirection)
	total := len(filtered)
	if offset > total {
		offset = total
	}
	end := min(offset+limit, total)
	files := filtered[offset:end]
	c.enrichGcodeFileList(ctx, files, includeMetadata, includeThumbnails)
	payload["offset"] = offset
	payload["files"] = files
	payload["directories"] = directoriesFromGcodeFiles(allFiles)
	payload["storage"] = c.gcodeStorage(ctx)
	payload["total"] = total
	payload["has_more"] = end < total
	payload["summary"] = gcodeFilesSummary(total)
	c.gcodeFiles.set(cacheKey, payload, gcodeFilesCacheTTL)
	return copyMap(payload)
}

func normalizeGcodeFileList(raw any) []map[string]any {
	items := unwrapGcodeFileItems(raw)
	files := make([]map[string]any, 0, len(items))
	for _, item := range items {
		file := compactGcodeFile(item)
		filename := normalizedMoonrakerGcodePath(firstString(file, "path", "filename"))
		if filename == "" || !isGcodeFileName(filename) {
			continue
		}
		file["filename"] = filename
		file["path"] = filename
		files = append(files, file)
	}
	return files
}

func (c *MoonrakerClient) enrichGcodeFileList(ctx context.Context, files []map[string]any, includeMetadata bool, includeThumbnails bool) {
	thumbnailLimit := min(len(files), maxGcodeFileThumbnailRequests)
	var wait sync.WaitGroup
	semaphore := make(chan struct{}, gcodeFileEnrichmentConcurrency)
	for index, file := range files {
		index := index
		file := file
		wait.Add(1)
		go func() {
			defer wait.Done()
			select {
			case semaphore <- struct{}{}:
				defer func() { <-semaphore }()
			case <-ctx.Done():
				return
			}
			var metadata map[string]any
			filename := stringValue(file["filename"])
			if includeMetadata {
				metadata = c.gcodeFileMetadata(ctx, filename)
				mergeGcodeMetadata(file, metadata)
			}
			if includeThumbnails && index < thumbnailLimit {
				file["thumbnail"] = c.gcodeFileThumbnail(ctx, filename, metadata)
			}
		}()
	}
	wait.Wait()
}

func filterGcodeFiles(files []map[string]any, directory string, query string) []map[string]any {
	filtered := make([]map[string]any, 0, len(files))
	for _, file := range files {
		filename := stringValue(file["filename"])
		if directory != "" && parentDirectory(filename) != directory {
			continue
		}
		if query != "" && !strings.Contains(strings.ToLower(filename), query) {
			continue
		}
		filtered = append(filtered, file)
	}
	return filtered
}

func sortGcodeFiles(files []map[string]any, sortKey string, direction string) {
	descending := direction != "asc"
	sort.SliceStable(files, func(i, j int) bool {
		switch sortKey {
		case "name":
			left := strings.ToLower(stringValue(files[i]["filename"]))
			right := strings.ToLower(stringValue(files[j]["filename"]))
			if descending {
				return left > right
			}
			return left < right
		case "size":
			left, _ := numberFromAny(files[i]["size"])
			right, _ := numberFromAny(files[j]["size"])
			if descending {
				return left > right
			}
			return left < right
		default:
			left, _ := numberFromAny(files[i]["modified"])
			right, _ := numberFromAny(files[j]["modified"])
			if descending {
				return left > right
			}
			return left < right
		}
	})
}

func (c *MoonrakerClient) gcodeFileMetadata(ctx context.Context, filename string) map[string]any {
	payload := map[string]any{}
	if err := c.get(ctx, "/server/files/metadata?filename="+url.QueryEscape(filename), "file_metadata", payload); err != nil {
		return nil
	}
	return mapValue(nestedAny(payload["file_metadata"], "result"))
}

func mergeGcodeMetadata(file map[string]any, metadata map[string]any) {
	if len(metadata) == 0 {
		file["metadata_available"] = false
		return
	}
	file["metadata_available"] = true
	for _, item := range []struct {
		target string
		keys   []string
	}{
		{"estimated_time", []string{"estimated_time"}},
		{"slicer", []string{"slicer"}},
		{"slicer_version", []string{"slicer_version"}},
		{"object_height", []string{"object_height"}},
		{"layer_height", []string{"layer_height"}},
		{"first_layer_height", []string{"first_layer_height"}},
		{"layer_count", []string{"layer_count", "layers", "total_layers", "total_layer"}},
		{"nozzle_diameter", []string{"nozzle_diameter"}},
		{"filament_total", []string{"filament_total"}},
		{"filament_weight_total", []string{"filament_weight_total"}},
		{"filament_type", []string{"filament_type"}},
		{"filament_name", []string{"filament_name"}},
		{"first_layer_bed_temp", []string{"first_layer_bed_temp", "bed_temp", "bed_temperature"}},
		{"first_layer_extr_temp", []string{"first_layer_extr_temp", "extruder_temp", "extruder_temperature"}},
		{"print_start_time", []string{"print_start_time"}},
		{"print_end_time", []string{"print_end_time"}},
		{"last_print_duration", []string{"last_print_duration", "print_duration"}},
	} {
		if file[item.target] != nil && file[item.target] != "" {
			continue
		}
		if textTarget(item.target) {
			file[item.target] = firstString(metadata, item.keys...)
		} else {
			file[item.target] = firstNumber(metadata, item.keys...)
		}
	}
}

func textTarget(key string) bool {
	return key == "slicer" || key == "slicer_version" || key == "filament_type" || key == "filament_name"
}

func (c *MoonrakerClient) gcodeFileThumbnail(ctx context.Context, filename string, metadata map[string]any) map[string]any {
	candidates := c.thumbnailCandidates(ctx, filename, metadata)
	for _, candidate := range candidates {
		if candidate.path == "" || candidate.size > maxThumbnailDownloadBytes {
			continue
		}
		data, truncated, err := c.downloadMoonrakerFile(ctx, "gcodes", candidate.path, maxThumbnailDownloadBytes)
		if err != nil || truncated || len(data) == 0 {
			continue
		}
		dataURI, width, height := compactImageDataURI(data)
		if dataURI == "" {
			continue
		}
		if width == 0 {
			width = candidate.width
		}
		if height == 0 {
			height = candidate.height
		}
		return map[string]any{
			"data_uri": dataURI,
			"width":    width,
			"height":   height,
			"source":   "moonraker_thumbnail",
		}
	}
	return nil
}

func directoriesFromGcodeFiles(files []map[string]any) []any {
	type directoryStats struct {
		path      string
		name      string
		parent    string
		fileCount int
		totalSize float64
		modified  float64
	}
	byPath := map[string]*directoryStats{}
	for _, file := range files {
		filePath := stringValue(file["path"])
		size, hasSize := numberFromAny(file["size"])
		modified, hasModified := numberFromAny(file["modified"])
		parts := strings.Split(path.Dir(filePath), "/")
		if len(parts) == 1 && parts[0] == "." {
			continue
		}
		for index := 1; index <= len(parts); index++ {
			dirPath := strings.Join(parts[:index], "/")
			if strings.TrimSpace(dirPath) == "" {
				continue
			}
			stats := byPath[dirPath]
			if stats == nil {
				stats = &directoryStats{path: dirPath, name: path.Base(dirPath), parent: parentDirectory(dirPath)}
				byPath[dirPath] = stats
			}
			stats.fileCount++
			if hasSize {
				stats.totalSize += size
			}
			if hasModified && modified > stats.modified {
				stats.modified = modified
			}
		}
	}
	paths := make([]string, 0, len(byPath))
	for dirPath := range byPath {
		paths = append(paths, dirPath)
	}
	sort.Strings(paths)
	result := make([]any, 0, len(paths))
	for _, dirPath := range paths {
		stats := byPath[dirPath]
		result = append(result, map[string]any{
			"path":       stats.path,
			"name":       stats.name,
			"parent":     stats.parent,
			"file_count": stats.fileCount,
			"total_size": stats.totalSize,
			"modified":   stats.modified,
		})
	}
	return result
}

func (c *MoonrakerClient) gcodeStorage(ctx context.Context) map[string]any {
	payload := map[string]any{}
	_ = c.get(ctx, "/server/files/directory?path=gcodes", "directory", payload)
	result := mapValue(nestedAny(payload["directory"], "result"))
	diskUsage := mapValue(result["disk_usage"])
	if len(diskUsage) == 0 {
		diskUsage = result
	}
	storage := map[string]any{}
	for _, item := range []struct {
		target string
		keys   []string
	}{
		{"total", []string{"total", "total_bytes", "total_space"}},
		{"used", []string{"used", "used_bytes", "used_space"}},
		{"free", []string{"free", "free_bytes", "free_space"}},
	} {
		storage[item.target] = firstNumber(diskUsage, item.keys...)
	}
	if storage["total"] == nil && storage["used"] == nil && storage["free"] == nil {
		return nil
	}
	return storage
}

func gcodeFilesSummary(total int) string {
	if total == 0 {
		return "Nenhum arquivo G-code retornado pelo Moonraker."
	}
	return strings.TrimSpace(strings.Join([]string{intString(total), "arquivo(s) G-code retornado(s) pelo Moonraker."}, " "))
}

func (c *gcodeFilesListCache) get(key string) map[string]any {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.payload == nil || c.key != key || time.Now().After(c.expiresAt) {
		return nil
	}
	return copyMap(c.payload)
}

func (c *gcodeFilesListCache) set(key string, payload map[string]any, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.key = key
	c.payload = copyMap(payload)
	c.expiresAt = time.Now().Add(ttl)
}

func copyMap(value map[string]any) map[string]any {
	if value == nil {
		return nil
	}
	result := make(map[string]any, len(value))
	for key, item := range value {
		result[key] = item
	}
	return result
}

func normalizedMoonrakerGcodePath(value string) string {
	cleaned := strings.TrimSpace(strings.ReplaceAll(value, "\\", "/"))
	if cleaned == "" {
		return ""
	}
	parts := make([]string, 0)
	for _, part := range strings.Split(cleaned, "/") {
		part = strings.TrimSpace(part)
		if part == "" || part == "." || part == ".." {
			continue
		}
		parts = append(parts, part)
	}
	return strings.Join(parts, "/")
}

func normalizedMoonrakerDirectoryPath(value string) string {
	cleaned := normalizedMoonrakerGcodePath(value)
	if cleaned == "gcodes" {
		return ""
	}
	return strings.TrimPrefix(cleaned, "gcodes/")
}

func normalizedGcodeFileSortKey(value string) string {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "name", "size":
		return strings.ToLower(strings.TrimSpace(value))
	default:
		return "modified"
	}
}

func normalizedGcodeFileSortDirection(value string) string {
	if strings.EqualFold(strings.TrimSpace(value), "asc") {
		return "asc"
	}
	return "desc"
}

func parentDirectory(value string) string {
	parent := path.Dir(value)
	if parent == "." {
		return ""
	}
	return parent
}

func boolFromAny(value any) bool {
	typed, ok := value.(bool)
	return ok && typed
}

func intString(value int) string {
	return strconv.Itoa(value)
}
