package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

func GetCourses(ctx context.Context, page, limit uint) (CourseResponse, error) {
	urlCourses := "https://jarvis-v2.ed.team/v2/public/cache-edql"
	body := []byte(fmt.Sprintf(`{"name":"cache:GENERAL:page(%d):limit(%d):key(COURSES_GRID_PAGINATION)"}`, page, limit))
	statusCode, responseBody, err := Request(ctx, http.MethodPost, urlCourses, "", body)
	if err != nil {
		return CourseResponse{}, err
	}
	if statusCode != http.StatusOK {
		return CourseResponse{}, fmt.Errorf("unexpected status code: %d", statusCode)
	}
	// Parse the response
	var courses CourseResponse
	err = json.Unmarshal(responseBody, &courses)
	if err != nil {
		return CourseResponse{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return courses, nil
}
