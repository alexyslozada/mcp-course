package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
)

func Request(ctx context.Context, method, url, token string, data any) (int, []byte, error) {
	var body []byte
	if data != nil {
		// If `data` is a slice of bytes, set it directly
		if b, ok := data.([]byte); ok {
			body = b
		} else {
			var err error
			body, err = json.Marshal(data)
			if err != nil {
				return 0, nil, fmt.Errorf("failed to marshal data: %w", err)
			}
		}
	}

	req, err := http.NewRequest(method, url, bytes.NewReader(body))
	if err != nil {
		return 0, nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	if token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", token))
	}
	req = req.WithContext(ctx)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return 0, nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer func(resp *http.Response) {
		errClose := resp.Body.Close()
		if errClose != nil {
			log.Printf("failed to close response body errClose: %v", errClose)
		}
	}(resp)

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, nil, fmt.Errorf("failed to read response body: %w", err)
	}

	return resp.StatusCode, respBody, nil
}
