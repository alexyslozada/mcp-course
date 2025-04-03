package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

func AddCourseToShoppingCart(ctx context.Context, token string, courseID int) (ShoppingCartResponse, error) {
	urlShoppingCart := "https://billing-v2.ed.team/v2/private/shopping-carts"
	body := []byte(fmt.Sprintf(`{"course_id":%d}`, courseID))
	statusCode, responseBody, err := Request(ctx, http.MethodPost, urlShoppingCart, token, body)
	if err != nil {
		return ShoppingCartResponse{}, err
	}
	if statusCode != http.StatusCreated {
		return ShoppingCartResponse{}, fmt.Errorf("unexpected status code: %d", statusCode)
	}
	// Parse the response
	var shoppingCart ShoppingCartResponse
	err = json.Unmarshal(responseBody, &shoppingCart)
	if err != nil {
		return ShoppingCartResponse{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return shoppingCart, nil
}
