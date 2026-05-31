package agent

import (
	"io"
	"log"
	"os"
	"path/filepath"
	"regexp"
)

var secretPattern = regexp.MustCompile(`ptr_(agent|pair|sess)_[A-Za-z0-9_\-]+`)

type RedactingWriter struct {
	Writer io.Writer
}

func (w RedactingWriter) Write(p []byte) (int, error) {
	redacted := secretPattern.ReplaceAll(p, []byte("ptr_$1_[REDACTED]"))
	_, err := w.Writer.Write(redacted)
	return len(p), err
}

func NewLogger(path string) (*log.Logger, io.Closer, error) {
	if path == "" {
		return log.New(RedactingWriter{Writer: os.Stdout}, "", log.LstdFlags), io.NopCloser(nil), nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return nil, nil, err
	}
	if err := rotateLog(path, 512*1024); err != nil {
		return nil, nil, err
	}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return nil, nil, err
	}
	return log.New(RedactingWriter{Writer: file}, "", log.LstdFlags), file, nil
}

func rotateLog(path string, maxBytes int64) error {
	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	if info.Size() < maxBytes {
		return nil
	}
	_ = os.Remove(path + ".1")
	return os.Rename(path, path+".1")
}
