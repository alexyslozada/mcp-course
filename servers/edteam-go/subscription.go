package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

func GetSubscription(ctx context.Context, token string) (SubscriptionResponse, error) {
	urlSubscriptions := "https://api.ed.team/api/v1/subscriptions/historical"
	statusCode, responseBody, err := Request(ctx, http.MethodGet, urlSubscriptions, token, nil)
	if err != nil {
		return SubscriptionResponse{}, err
	}
	if statusCode != http.StatusOK {
		return SubscriptionResponse{}, fmt.Errorf("unexpected status code: %d", statusCode)
	}
	// Parse the response
	var subscriptions SubscriptionResponse
	err = json.Unmarshal(responseBody, &subscriptions)
	if err != nil {
		return SubscriptionResponse{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return subscriptions, nil
}
