package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

func ProcessLogin(ctx context.Context, email, password string) (string, error) {
	login := Login{
		Email:    email,
		Password: password,
	}

	// Make the request
	urlLogin := "https://api.ed.team/api/v1/login"
	statusCode, responseBody, err := Request(ctx, http.MethodPost, urlLogin, "", login)
	if err != nil {
		return "", err
	}
	if statusCode != http.StatusOK {
		return "", fmt.Errorf("unexpected status code: %d", statusCode)
	}
	// Parse the response
	var response LoginResponse
	err = json.Unmarshal(responseBody, &response)
	if err != nil {
		return "", fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return response.Data.Token, nil
}
