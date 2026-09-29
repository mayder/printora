package agent

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/jpeg"
	"io"
	"math"
	"net/http"
	"net/url"
	"path"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	_ "image/gif"
	_ "image/png"
)

const maxPreviewGcodeBytes = 24 * 1024 * 1024
const maxThumbnailDownloadBytes = 512 * 1024
const maxThumbnailDataURIBytes = 32000
const maxLayerSVGBytes = 12000
const maxStoredGcodeSegments = 80000
const maxScenePrintedSegments = 4200
const maxSceneCurrentSegments = 2400
const maxSceneFutureSegments = 1400

const (
	gcodeLineTypeUnknown = iota
	gcodeLineTypeOuterWall
	gcodeLineTypeInnerWall
	gcodeLineTypeSparseInfill
	gcodeLineTypeSolidInfill
	gcodeLineTypeTopSurface
	gcodeLineTypeSupport
	gcodeLineTypeSkirt
	gcodeLineTypeBridge
)

type operationVisualCache struct {
	mu        sync.Mutex
	filename  string
	thumbnail map[string]any
	parsed    *gcodePreview
}

type gcodePreview struct {
	filename      string
	layers        []gcodeLayer
	minX          float64
	minY          float64
	maxX          float64
	maxY          float64
	truncated     bool
	segmentCount  int
	lastGenerated time.Time
}

type gcodeLayer struct {
	z        float64
	segments []gcodeSegment
}

type gcodeSegment struct {
	x1       float64
	y1       float64
	x2       float64
	y2       float64
	lineType int
}

func (c *MoonrakerClient) enrichOperationVisuals(ctx context.Context, filename string, payload map[string]any) {
	metadata := ensureFileMetadataResult(payload, filename)
	currentLayer, totalLayers := operationLayerNumbers(payload, metadata)
	visuals := c.operationVisuals(ctx, filename, metadata, currentLayer, totalLayers)
	if len(visuals) == 0 {
		return
	}
	metadata["printora_visuals"] = visuals
}

func ensureFileMetadataResult(payload map[string]any, filename string) map[string]any {
	wrapper := mapValue(payload["file_metadata"])
	result := mapValue(wrapper["result"])
	if len(result) == 0 {
		result = map[string]any{"filename": filename}
		wrapper["result"] = result
		payload["file_metadata"] = wrapper
	}
	return result
}

func (c *MoonrakerClient) operationVisuals(ctx context.Context, filename string, metadata map[string]any, currentLayer int, totalLayers int) map[string]any {
	c.visuals.mu.Lock()
	defer c.visuals.mu.Unlock()
	if c.visuals.filename != filename {
		c.visuals.filename = filename
		c.visuals.thumbnail = nil
		c.visuals.parsed = nil
	}
	result := map[string]any{}
	if c.visuals.thumbnail == nil {
		c.visuals.thumbnail = c.fetchThumbnailVisual(ctx, filename, metadata)
	}
	if len(c.visuals.thumbnail) > 0 {
		result["thumbnail"] = c.visuals.thumbnail
	}
	if currentLayer > 0 {
		if c.visuals.parsed == nil {
			c.visuals.parsed = c.fetchGcodePreview(ctx, filename)
		}
		if c.visuals.parsed != nil {
			if layer := c.visuals.parsed.layerVisual(currentLayer, totalLayers); len(layer) > 0 {
				result["layer_preview"] = layer
			}
		}
	}
	return result
}

func (c *MoonrakerClient) fetchThumbnailVisual(ctx context.Context, filename string, metadata map[string]any) map[string]any {
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

type thumbnailCandidate struct {
	path   string
	width  int
	height int
	size   int
}

func (c *MoonrakerClient) thumbnailCandidates(ctx context.Context, filename string, metadata map[string]any) []thumbnailCandidate {
	payload := map[string]any{}
	_ = c.get(ctx, "/server/files/thumbnails?filename="+url.QueryEscape(filename), "thumbnails", payload)
	candidates := readThumbnailDetails(payload["thumbnails"])
	if len(candidates) == 0 {
		candidates = readMetadataThumbnails(filename, metadata["thumbnails"])
	}
	sort.SliceStable(candidates, func(i int, j int) bool {
		return candidates[i].width*candidates[i].height > candidates[j].width*candidates[j].height
	})
	return candidates
}

func readThumbnailDetails(value any) []thumbnailCandidate {
	if result := nestedAny(value, "result"); result != nil {
		value = result
	}
	items, ok := value.([]any)
	if !ok {
		return nil
	}
	candidates := make([]thumbnailCandidate, 0, len(items))
	for _, item := range items {
		row := mapValue(item)
		candidates = append(candidates, thumbnailCandidate{
			path:   strings.TrimSpace(stringValue(row["thumbnail_path"])),
			width:  intFromAny(row["width"]),
			height: intFromAny(row["height"]),
			size:   intFromAny(row["size"]),
		})
	}
	return candidates
}

func readMetadataThumbnails(filename string, value any) []thumbnailCandidate {
	items, ok := value.([]any)
	if !ok {
		return nil
	}
	baseDir := path.Dir(strings.TrimSpace(filename))
	if baseDir == "." {
		baseDir = ""
	}
	candidates := make([]thumbnailCandidate, 0, len(items))
	for _, item := range items {
		row := mapValue(item)
		relative := strings.TrimSpace(stringValue(row["relative_path"]))
		if relative == "" {
			continue
		}
		candidatePath := path.Clean(path.Join(baseDir, relative))
		if candidatePath == ".." || strings.HasPrefix(candidatePath, "../") {
			continue
		}
		candidates = append(candidates, thumbnailCandidate{
			path:   candidatePath,
			width:  intFromAny(row["width"]),
			height: intFromAny(row["height"]),
			size:   intFromAny(row["size"]),
		})
	}
	return candidates
}

func compactImageDataURI(data []byte) (string, int, int) {
	img, _, err := image.Decode(bytes.NewReader(data))
	if err != nil {
		if len(data) > 12000 {
			return "", 0, 0
		}
		mime := http.DetectContentType(data)
		return "data:" + mime + ";base64," + base64.StdEncoding.EncodeToString(data), 0, 0
	}
	for _, option := range []struct {
		maxDim  int
		quality int
	}{
		{360, 78},
		{320, 74},
		{280, 70},
		{220, 68},
	} {
		resized := resizeImageNearest(img, option.maxDim)
		var out bytes.Buffer
		if err := jpeg.Encode(&out, resized, &jpeg.Options{Quality: option.quality}); err != nil {
			continue
		}
		dataURI := "data:image/jpeg;base64," + base64.StdEncoding.EncodeToString(out.Bytes())
		if len(dataURI) <= maxThumbnailDataURIBytes {
			return dataURI, resized.Bounds().Dx(), resized.Bounds().Dy()
		}
	}
	return "", 0, 0
}

func resizeImageNearest(src image.Image, maxDim int) *image.RGBA {
	bounds := src.Bounds()
	width := bounds.Dx()
	height := bounds.Dy()
	if width <= 0 || height <= 0 {
		return image.NewRGBA(image.Rect(0, 0, 1, 1))
	}
	scale := math.Min(1, float64(maxDim)/float64(max(width, height)))
	outW := max(1, int(math.Round(float64(width)*scale)))
	outH := max(1, int(math.Round(float64(height)*scale)))
	dst := image.NewRGBA(image.Rect(0, 0, outW, outH))
	bg := color.RGBA{R: 15, G: 23, B: 32, A: 255}
	for y := 0; y < outH; y++ {
		for x := 0; x < outW; x++ {
			sx := bounds.Min.X + min(width-1, int(float64(x)/scale))
			sy := bounds.Min.Y + min(height-1, int(float64(y)/scale))
			dst.SetRGBA(x, y, compositeOnBackground(src.At(sx, sy), bg))
		}
	}
	return dst
}

func compositeOnBackground(src color.Color, bg color.RGBA) color.RGBA {
	r, g, b, a := src.RGBA()
	alpha := float64(a) / 65535
	return color.RGBA{
		R: uint8(float64(uint8(r>>8))*alpha + float64(bg.R)*(1-alpha)),
		G: uint8(float64(uint8(g>>8))*alpha + float64(bg.G)*(1-alpha)),
		B: uint8(float64(uint8(b>>8))*alpha + float64(bg.B)*(1-alpha)),
		A: 255,
	}
}

func (c *MoonrakerClient) fetchGcodePreview(ctx context.Context, filename string) *gcodePreview {
	data, truncated, err := c.downloadMoonrakerFile(ctx, "gcodes", filename, maxPreviewGcodeBytes)
	if err != nil || len(data) == 0 {
		return nil
	}
	preview := parseGcodePreview(filename, data, truncated)
	if preview.segmentCount == 0 {
		return nil
	}
	return preview
}

func (c *MoonrakerClient) downloadMoonrakerFile(ctx context.Context, root string, relativePath string, limit int64) ([]byte, bool, error) {
	target, err := url.JoinPath(c.baseURL, "server", "files", root)
	if err != nil {
		return nil, false, err
	}
	target = strings.TrimRight(target, "/") + "/" + escapePathSegments(relativePath)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return nil, false, err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, false, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, false, fmt.Errorf("moonraker file %s/%s: status %d", root, relativePath, resp.StatusCode)
	}
	data, err := io.ReadAll(io.LimitReader(resp.Body, limit+1))
	if err != nil {
		return nil, false, err
	}
	if int64(len(data)) > limit {
		return data[:limit], true, nil
	}
	return data, false, nil
}

func escapePathSegments(value string) string {
	parts := strings.Split(strings.TrimPrefix(strings.ReplaceAll(value, "\\", "/"), "/"), "/")
	escaped := make([]string, 0, len(parts))
	for _, part := range parts {
		if part == "" || part == "." || part == ".." {
			continue
		}
		escaped = append(escaped, url.PathEscape(part))
	}
	return strings.Join(escaped, "/")
}

func parseGcodePreview(filename string, data []byte, truncated bool) *gcodePreview {
	parser := newGcodeParser(filename, truncated)
	scanner := bufio.NewScanner(bytes.NewReader(data))
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for scanner.Scan() {
		if parser.done {
			break
		}
		parser.consume(scanner.Text())
	}
	parser.finish()
	return parser.preview
}

type gcodeParser struct {
	preview           *gcodePreview
	x                 float64
	y                 float64
	z                 float64
	e                 float64
	haveXY            bool
	absolutePosition  bool
	absoluteExtrusion bool
	pendingLayer      bool
	done              bool
	lineType          int
}

func newGcodeParser(filename string, truncated bool) *gcodeParser {
	preview := &gcodePreview{
		filename:      filename,
		layers:        []gcodeLayer{{z: 0}},
		minX:          math.Inf(1),
		minY:          math.Inf(1),
		maxX:          math.Inf(-1),
		maxY:          math.Inf(-1),
		truncated:     truncated,
		lastGenerated: time.Now(),
	}
	return &gcodeParser{preview: preview, absolutePosition: true, absoluteExtrusion: true}
}

func (p *gcodeParser) consume(line string) {
	trimmed := strings.TrimSpace(line)
	if trimmed == "" {
		return
	}
	if strings.HasPrefix(trimmed, ";") {
		p.consumeComment(trimmed)
		return
	}
	commandLine := strings.TrimSpace(strings.SplitN(trimmed, ";", 2)[0])
	if commandLine == "" {
		return
	}
	fields := strings.Fields(commandLine)
	if len(fields) == 0 {
		return
	}
	command := strings.ToUpper(fields[0])
	params := gcodeParams(fields[1:])
	switch command {
	case "G90":
		p.absolutePosition = true
	case "G91":
		p.absolutePosition = false
	case "M82":
		p.absoluteExtrusion = true
	case "M83":
		p.absoluteExtrusion = false
	case "G92":
		if value, ok := params["E"]; ok {
			p.e = value
		}
	case "G0", "G1":
		p.consumeMove(params)
	}
}

func (p *gcodeParser) consumeComment(line string) {
	upper := strings.ToUpper(strings.TrimSpace(line))
	if lineType, ok := gcodeLineTypeFromComment(upper); ok {
		p.lineType = lineType
	}
	switch {
	case strings.HasPrefix(upper, ";LAYER:"):
		if layer, err := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(upper, ";LAYER:"))); err == nil {
			p.setCurrentLayer(max(0, layer))
		}
	case upper == ";LAYER_CHANGE" || strings.HasPrefix(upper, ";LAYER_CHANGE "):
		p.pendingLayer = true
	case strings.HasPrefix(upper, ";Z:") && p.pendingLayer:
		if z, err := strconv.ParseFloat(strings.TrimSpace(strings.TrimPrefix(upper, ";Z:")), 64); err == nil {
			p.startLayer(z)
			p.pendingLayer = false
		}
	}
}

func (p *gcodeParser) consumeMove(params map[string]float64) {
	oldX, oldY, oldZ, oldE := p.x, p.y, p.z, p.e
	newX, newY, newZ, newE := oldX, oldY, oldZ, oldE
	if value, ok := params["X"]; ok {
		newX = axisValue(oldX, value, p.absolutePosition)
	}
	if value, ok := params["Y"]; ok {
		newY = axisValue(oldY, value, p.absolutePosition)
	}
	if value, ok := params["Z"]; ok {
		newZ = axisValue(oldZ, value, p.absolutePosition)
	}
	if value, ok := params["E"]; ok {
		if p.absoluteExtrusion {
			newE = value
		} else {
			newE = oldE + value
		}
	}
	if p.pendingLayer && (newZ > oldZ+0.0005 || p.currentLayerHasSegments()) {
		p.startLayer(newZ)
		p.pendingLayer = false
	} else if newZ > oldZ+0.001 && p.currentLayerHasSegments() {
		p.startLayer(newZ)
	}
	extruding := extrusionDelta(oldE, newE, params, p.absoluteExtrusion) > 0.000001
	if p.haveXY && extruding && (math.Abs(newX-oldX) > 0.0001 || math.Abs(newY-oldY) > 0.0001) {
		p.addSegment(gcodeSegment{x1: oldX, y1: oldY, x2: newX, y2: newY, lineType: p.lineType})
	}
	if _, ok := params["X"]; ok {
		p.haveXY = true
	}
	if _, ok := params["Y"]; ok {
		p.haveXY = true
	}
	p.x, p.y, p.z, p.e = newX, newY, newZ, newE
}

func gcodeLineTypeFromComment(line string) (int, bool) {
	comment := strings.TrimSpace(strings.TrimPrefix(line, ";"))
	for _, prefix := range []string{"TYPE:", "FEATURE:"} {
		if strings.HasPrefix(comment, prefix) {
			return classifyGcodeLineType(strings.TrimSpace(strings.TrimPrefix(comment, prefix))), true
		}
	}
	return gcodeLineTypeUnknown, false
}

func classifyGcodeLineType(value string) int {
	normalized := strings.NewReplacer("_", " ", "-", " ", "/", " ").Replace(strings.ToUpper(value))
	switch {
	case containsAny(normalized, "OUTER WALL", "WALL OUTER", "EXTERNAL WALL", "EXTERNAL PERIMETER", "OUTER PERIMETER"):
		return gcodeLineTypeOuterWall
	case containsAny(normalized, "INNER WALL", "WALL INNER", "INNER PERIMETER", "PERIMETER"):
		return gcodeLineTypeInnerWall
	case containsAny(normalized, "TOP SURFACE", "TOP SOLID", "TOP INFILL"):
		return gcodeLineTypeTopSurface
	case containsAny(normalized, "INTERNAL SOLID", "SOLID INFILL", "BOTTOM SURFACE", "SKIN", "GAP FILL"):
		return gcodeLineTypeSolidInfill
	case containsAny(normalized, "SPARSE INFILL", "INTERNAL INFILL", "INFILL", "FILL"):
		return gcodeLineTypeSparseInfill
	case containsAny(normalized, "SUPPORT"):
		return gcodeLineTypeSupport
	case containsAny(normalized, "SKIRT", "BRIM", "PRIME TOWER", "CUSTOM"):
		return gcodeLineTypeSkirt
	case containsAny(normalized, "BRIDGE"):
		return gcodeLineTypeBridge
	default:
		return gcodeLineTypeUnknown
	}
}

func containsAny(value string, needles ...string) bool {
	for _, needle := range needles {
		if strings.Contains(value, needle) {
			return true
		}
	}
	return false
}

func (p *gcodeParser) startLayer(z float64) {
	if !p.currentLayerHasSegments() {
		p.preview.layers[len(p.preview.layers)-1].z = z
		return
	}
	p.preview.layers = append(p.preview.layers, gcodeLayer{z: z})
}

func (p *gcodeParser) setCurrentLayer(index int) {
	for len(p.preview.layers) <= index {
		p.preview.layers = append(p.preview.layers, gcodeLayer{})
	}
}

func (p *gcodeParser) currentLayerHasSegments() bool {
	return len(p.preview.layers[len(p.preview.layers)-1].segments) > 0
}

func (p *gcodeParser) addSegment(segment gcodeSegment) {
	if p.preview.segmentCount >= maxStoredGcodeSegments {
		p.preview.truncated = true
		p.done = true
		return
	}
	index := len(p.preview.layers) - 1
	p.preview.layers[index].segments = append(p.preview.layers[index].segments, segment)
	p.preview.segmentCount++
	p.preview.minX = math.Min(p.preview.minX, math.Min(segment.x1, segment.x2))
	p.preview.minY = math.Min(p.preview.minY, math.Min(segment.y1, segment.y2))
	p.preview.maxX = math.Max(p.preview.maxX, math.Max(segment.x1, segment.x2))
	p.preview.maxY = math.Max(p.preview.maxY, math.Max(segment.y1, segment.y2))
}

func (p *gcodeParser) finish() {
	layers := p.preview.layers[:0]
	for _, layer := range p.preview.layers {
		if len(layer.segments) > 0 {
			layers = append(layers, layer)
		}
	}
	p.preview.layers = layers
}

func gcodeParams(fields []string) map[string]float64 {
	params := map[string]float64{}
	for _, field := range fields {
		if len(field) < 2 {
			continue
		}
		key := strings.ToUpper(field[:1])
		if key < "A" || key > "Z" {
			continue
		}
		value, err := strconv.ParseFloat(field[1:], 64)
		if err == nil {
			params[key] = value
		}
	}
	return params
}

func axisValue(current float64, value float64, absolute bool) float64 {
	if absolute {
		return value
	}
	return current + value
}

func extrusionDelta(oldE float64, newE float64, params map[string]float64, absolute bool) float64 {
	if !absolute {
		return params["E"]
	}
	return newE - oldE
}

func (p *gcodePreview) layerVisual(currentLayer int, totalLayers int) map[string]any {
	if len(p.layers) == 0 || p.segmentCount == 0 {
		return nil
	}
	index := min(max(0, currentLayer-1), len(p.layers)-1)
	total := totalLayers
	if total <= 0 {
		total = len(p.layers)
	}
	svg := p.layerSVG(index)
	if svg == "" {
		return nil
	}
	return map[string]any{
		"data_uri":      "data:image/svg+xml;base64," + base64.StdEncoding.EncodeToString([]byte(svg)),
		"current_layer": currentLayer,
		"total_layers":  total,
		"projection":    "isometric",
		"scene":         p.layerScene(index, currentLayer, total),
		"source":        "agent_gcode",
		"truncated":     p.truncated,
	}
}

func (p *gcodePreview) layerScene(index int, currentLayer int, totalLayers int) map[string]any {
	if index < 0 || index >= len(p.layers) {
		return nil
	}
	printedLimit := maxScenePrintedSegments
	futureLimit := maxSceneFutureSegments
	if totalLayers > 0 && currentLayer >= totalLayers {
		printedLimit += maxSceneFutureSegments
		futureLimit = 0
	}
	printed, printedTotal := sampleSceneSegments(p.layers[:index], printedLimit)
	current, currentTotal := sampleSceneSegments(p.layers[index:index+1], maxSceneCurrentSegments)
	var future []sceneSegment
	futureTotal := 0
	if futureLimit > 0 {
		future, futureTotal = sampleSceneSegments(p.layers[min(index+1, len(p.layers)):], futureLimit)
	}
	if len(printed) == 0 && len(current) == 0 {
		return nil
	}
	return map[string]any{
		"kind":                    "gcode_layer_scene",
		"units":                   "mm",
		"bed":                     []float64{roundSceneCoord(p.minX), roundSceneCoord(p.minY), roundSceneCoord(p.maxX), roundSceneCoord(p.maxY)},
		"printed":                 encodeSceneSegments(printed),
		"current":                 encodeSceneSegments(current),
		"future":                  encodeSceneSegments(future),
		"current_layer":           currentLayer,
		"total_layers":            totalLayers,
		"current_layer_z":         roundSceneCoord(p.layers[index].z),
		"printed_segment_count":   printedTotal,
		"current_segment_count":   currentTotal,
		"future_segment_count":    futureTotal,
		"displayed_segment_count": len(printed) + len(current) + len(future),
		"total_segment_count":     p.segmentCount,
		"sampled":                 p.truncated || printedTotal > len(printed) || currentTotal > len(current) || futureTotal > len(future),
	}
}

func (p *gcodePreview) layerSVG(index int) string {
	previous := sampleProjectedSegments(projectLayerSegments(p.layers[:index]), 90)
	current := sampleProjectedSegments(projectLayerSegments(p.layers[index:index+1]), 300)
	if len(previous) == 0 && len(current) == 0 {
		return ""
	}
	bed := projectedBed(p.minX, p.minY, p.maxX, p.maxY)
	bounds := projectedBounds(append(append([]projectedSegment{}, previous...), append(current, bed...)...))
	width := math.Max(1, bounds.maxX-bounds.minX)
	height := math.Max(1, bounds.maxY-bounds.minY)
	padding := math.Max(8, math.Max(width, height)*0.06)
	viewX := bounds.minX - padding
	viewY := bounds.minY - padding
	viewW := width + padding*2
	viewH := height + padding*2
	svg := fmt.Sprintf(
		`<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f"><rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="2" fill="#0f1720"/><g fill="none" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke">`,
		viewX, viewY, viewW, viewH, viewX, viewY, viewW, viewH,
	)
	if len(bed) > 0 {
		svg += `<path d="` + projectedSegmentsPath(bed) + `" stroke="#334155" stroke-width="1.2" opacity="0.55"/>`
	}
	if len(previous) > 0 {
		svg += `<path d="` + projectedSegmentsPath(previous) + `" stroke="#64748b" stroke-width="1.1" opacity="0.34"/>`
	}
	if len(current) > 0 {
		svg += `<path d="` + projectedSegmentsPath(current) + `" stroke="#22d3ee" stroke-width="1.9" opacity="0.98"/>`
	}
	svg += `</g></svg>`
	if len(svg) > maxLayerSVGBytes {
		current = sampleProjectedSegments(current, 200)
		previous = sampleProjectedSegments(previous, 50)
		return compactLayerSVG(viewX, viewY, viewW, viewH, bed, previous, current)
	}
	return svg
}

func compactLayerSVG(viewX float64, viewY float64, viewW float64, viewH float64, bed []projectedSegment, previous []projectedSegment, current []projectedSegment) string {
	svg := fmt.Sprintf(
		`<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.1f %.1f %.1f %.1f"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#0f1720"/><g fill="none" stroke-linecap="round" vector-effect="non-scaling-stroke">`,
		viewX, viewY, viewW, viewH, viewX, viewY, viewW, viewH,
	)
	if len(bed) > 0 {
		svg += `<path d="` + projectedSegmentsPath(bed) + `" stroke="#334155" stroke-width="1" opacity=".5"/>`
	}
	if len(previous) > 0 {
		svg += `<path d="` + projectedSegmentsPath(previous) + `" stroke="#64748b" stroke-width="1" opacity=".32"/>`
	}
	if len(current) > 0 {
		svg += `<path d="` + projectedSegmentsPath(current) + `" stroke="#22d3ee" stroke-width="1.8"/>`
	}
	return svg + `</g></svg>`
}

type projectedSegment struct {
	x1 float64
	y1 float64
	x2 float64
	y2 float64
}

type projectedBoundsBox struct {
	minX float64
	minY float64
	maxX float64
	maxY float64
}

func projectLayerSegments(layers []gcodeLayer) []projectedSegment {
	count := 0
	for _, layer := range layers {
		count += len(layer.segments)
	}
	segments := make([]projectedSegment, 0, count)
	for _, layer := range layers {
		for _, segment := range layer.segments {
			segments = append(segments, projectSegment(segment, layer.z))
		}
	}
	return segments
}

func projectSegment(segment gcodeSegment, z float64) projectedSegment {
	x1, y1 := projectPoint(segment.x1, segment.y1, z)
	x2, y2 := projectPoint(segment.x2, segment.y2, z)
	return projectedSegment{x1: x1, y1: y1, x2: x2, y2: y2}
}

func projectPoint(x float64, y float64, z float64) (float64, float64) {
	return (x - y) * 0.866, (x+y)*0.5 - z*2.2
}

func projectedBed(minX float64, minY float64, maxX float64, maxY float64) []projectedSegment {
	if math.IsInf(minX, 0) || math.IsInf(minY, 0) || math.IsInf(maxX, 0) || math.IsInf(maxY, 0) {
		return nil
	}
	corners := [][2]float64{{minX, minY}, {maxX, minY}, {maxX, maxY}, {minX, maxY}, {minX, minY}}
	segments := make([]projectedSegment, 0, 4)
	for index := 0; index+1 < len(corners); index++ {
		x1, y1 := projectPoint(corners[index][0], corners[index][1], 0)
		x2, y2 := projectPoint(corners[index+1][0], corners[index+1][1], 0)
		segments = append(segments, projectedSegment{x1: x1, y1: y1, x2: x2, y2: y2})
	}
	return segments
}

func projectedBounds(segments []projectedSegment) projectedBoundsBox {
	bounds := projectedBoundsBox{minX: math.Inf(1), minY: math.Inf(1), maxX: math.Inf(-1), maxY: math.Inf(-1)}
	for _, segment := range segments {
		bounds.minX = math.Min(bounds.minX, math.Min(segment.x1, segment.x2))
		bounds.minY = math.Min(bounds.minY, math.Min(segment.y1, segment.y2))
		bounds.maxX = math.Max(bounds.maxX, math.Max(segment.x1, segment.x2))
		bounds.maxY = math.Max(bounds.maxY, math.Max(segment.y1, segment.y2))
	}
	if math.IsInf(bounds.minX, 0) {
		return projectedBoundsBox{minX: -1, minY: -1, maxX: 1, maxY: 1}
	}
	return bounds
}

func sampleProjectedSegments(segments []projectedSegment, limit int) []projectedSegment {
	if len(segments) <= limit || limit <= 0 {
		return segments
	}
	sampled := make([]projectedSegment, 0, limit)
	step := float64(len(segments)) / float64(limit)
	for index := 0; index < limit; index++ {
		sampled = append(sampled, segments[min(len(segments)-1, int(float64(index)*step))])
	}
	return sampled
}

type sceneSegment struct {
	x1       float64
	y1       float64
	z        float64
	x2       float64
	y2       float64
	lineType int
}

func sampleSceneSegments(layers []gcodeLayer, limit int) ([]sceneSegment, int) {
	segments := sceneSegments(layers)
	total := len(segments)
	if total <= limit || limit <= 0 {
		return segments, total
	}
	sampled := make([]sceneSegment, 0, limit)
	step := float64(total) / float64(limit)
	for index := 0; index < limit; index++ {
		sampled = append(sampled, segments[min(total-1, int(float64(index)*step))])
	}
	return sampled, total
}

func sceneSegments(layers []gcodeLayer) []sceneSegment {
	count := 0
	for _, layer := range layers {
		count += len(layer.segments)
	}
	segments := make([]sceneSegment, 0, count)
	for _, layer := range layers {
		for _, segment := range layer.segments {
			segments = append(segments, sceneSegment{x1: segment.x1, y1: segment.y1, z: layer.z, x2: segment.x2, y2: segment.y2, lineType: segment.lineType})
		}
	}
	return segments
}

func encodeSceneSegments(segments []sceneSegment) [][]float64 {
	encoded := make([][]float64, 0, len(segments))
	for _, segment := range segments {
		row := []float64{
			roundSceneCoord(segment.x1),
			roundSceneCoord(segment.y1),
			roundSceneCoord(segment.z),
			roundSceneCoord(segment.x2),
			roundSceneCoord(segment.y2),
			roundSceneCoord(segment.z),
		}
		if segment.lineType != gcodeLineTypeUnknown {
			row = append(row, float64(segment.lineType))
		}
		encoded = append(encoded, row)
	}
	return encoded
}

func roundSceneCoord(value float64) float64 {
	return math.Round(value*10) / 10
}

func projectedSegmentsPath(segments []projectedSegment) string {
	var builder strings.Builder
	for _, segment := range segments {
		builder.WriteString("M")
		builder.WriteString(formatCoord(segment.x1))
		builder.WriteByte(' ')
		builder.WriteString(formatCoord(segment.y1))
		builder.WriteString("L")
		builder.WriteString(formatCoord(segment.x2))
		builder.WriteByte(' ')
		builder.WriteString(formatCoord(segment.y2))
	}
	return builder.String()
}

func formatCoord(value float64) string {
	return strconv.FormatFloat(value, 'f', 1, 64)
}

func operationLayerNumbers(payload map[string]any, metadata map[string]any) (int, int) {
	status := mapValue(nestedAny(payload["operation_objects"], "result", "status"))
	printStats := mapValue(status["print_stats"])
	info := mapValue(printStats["info"])
	total := firstPositiveInt(printStats["total_layer"], info["total_layer"], info["total_layers"], metadata["layer_count"], metadata["total_layer"], metadata["total_layers"], metadata["layers"])
	if total <= 0 {
		total = estimatedTotalLayers(metadata)
	}
	if !operationHasMaterialProgress(status) {
		return 0, total
	}
	current := firstPositiveInt(printStats["current_layer"], info["current_layer"])
	if current <= 0 {
		current = estimatedLayerFromZ(status, metadata, total)
	}
	return current, total
}

func operationHasMaterialProgress(status map[string]any) bool {
	printStats := mapValue(status["print_stats"])
	display := mapValue(status["display_status"])
	virtualSD := mapValue(status["virtual_sdcard"])
	if filament, ok := numberFromAny(printStats["filament_used"]); ok {
		if filament > 0.01 {
			return true
		}
		if progress, ok := numberFromAny(display["progress"]); ok && normalizedOperationProgress(progress) > 0.001 {
			return true
		}
		return false
	}
	if progress, ok := numberFromAny(display["progress"]); ok && normalizedOperationProgress(progress) > 0.001 {
		return true
	}
	if progress, ok := numberFromAny(virtualSD["progress"]); ok && normalizedOperationProgress(progress) > 0.02 && !operationPrePrintMessage(status) {
		return true
	}
	return false
}

func normalizedOperationProgress(value float64) float64 {
	if value < 0 {
		return 0
	}
	if value <= 1 {
		return value
	}
	if value <= 100 {
		return value / 100
	}
	return 1
}

func operationPrePrintMessage(status map[string]any) bool {
	printStats := mapValue(status["print_stats"])
	display := mapValue(status["display_status"])
	normalized := strings.NewReplacer("-", "_", " ", "_").Replace(strings.ToLower(strings.TrimSpace(stringValue(printStats["message"]) + " " + stringValue(display["message"]))))
	for _, token := range []string{"qgl", "quad_gantry_level", "bed_mesh", "homing", "g28", "z_tilt", "calibrate_z"} {
		if strings.Contains(normalized, token) {
			return true
		}
	}
	return false
}

func estimatedLayerFromZ(status map[string]any, metadata map[string]any, total int) int {
	currentZ := currentZPosition(status)
	layerHeight, ok := numberFromAny(metadata["layer_height"])
	if !ok || layerHeight <= 0 || currentZ <= 0 {
		return 0
	}
	firstLayerHeight, ok := numberFromAny(metadata["first_layer_height"])
	if !ok || firstLayerHeight <= 0 {
		firstLayerHeight = layerHeight
	}
	current := 1
	if currentZ > firstLayerHeight+layerHeight*0.25 {
		current = 1 + int(math.Ceil(math.Max(0, currentZ-firstLayerHeight)/layerHeight))
	}
	if total > 0 {
		return min(max(1, current), total)
	}
	return max(1, current)
}

func estimatedTotalLayers(metadata map[string]any) int {
	objectHeight, okHeight := numberFromAny(metadata["object_height"])
	layerHeight, okLayer := numberFromAny(metadata["layer_height"])
	if !okHeight || !okLayer || objectHeight <= 0 || layerHeight <= 0 {
		return 0
	}
	firstLayerHeight, ok := numberFromAny(metadata["first_layer_height"])
	if !ok || firstLayerHeight <= 0 {
		firstLayerHeight = layerHeight
	}
	return max(1, 1+int(math.Ceil(math.Max(0, objectHeight-firstLayerHeight)/layerHeight)))
}

func currentZPosition(status map[string]any) float64 {
	for _, item := range []struct {
		object string
		field  string
	}{
		{"gcode_move", "gcode_position"},
		{"toolhead", "position"},
	} {
		values, ok := nestedAny(status, item.object, item.field).([]any)
		if !ok || len(values) <= 2 {
			continue
		}
		if z, ok := numberFromAny(values[2]); ok {
			return z
		}
	}
	return 0
}

func firstPositiveInt(values ...any) int {
	for _, value := range values {
		number := intFromAny(value)
		if number > 0 {
			return number
		}
	}
	return 0
}

func intFromAny(value any) int {
	number, ok := numberFromAny(value)
	if !ok {
		return 0
	}
	return int(number)
}

func numberFromAny(value any) (float64, bool) {
	switch typed := value.(type) {
	case float64:
		return typed, true
	case float32:
		return float64(typed), true
	case int:
		return float64(typed), true
	case int64:
		return float64(typed), true
	case json.Number:
		number, err := typed.Float64()
		return number, err == nil
	default:
		return 0, false
	}
}
