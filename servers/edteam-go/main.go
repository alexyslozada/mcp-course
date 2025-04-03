package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	log.SetOutput(os.Stderr)

	email := os.Getenv("EMAIL")
	password := os.Getenv("PASSWORD")
	if email == "" || password == "" {
		panic("EMAIL and PASSWORD environment variables must be set")
	}

	ctx := context.Background()
	token, err := ProcessLogin(ctx, email, password)
	if err != nil {
		panic(err)
	}

	// Create a new MCP server
	s := server.NewMCPServer(
		"EDteam API",
		"1.0.0",
		server.WithToolCapabilities(false),
		server.WithLogging(),
	)

	subscriptionsTool := mcp.NewTool(
		"Subscriptions",
		mcp.WithDescription("List all your subscriptions in the history of EDteam"),
	)

	s.AddTool(subscriptionsTool, func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		subscriptions, err := GetSubscription(ctx, token)
		if err != nil {
			return nil, err
		}
		var subscriptionsRaw []byte
		subscriptionsRaw, err = json.Marshal(subscriptions)
		if err != nil {
			return nil, err
		}

		return mcp.NewToolResultText(string(subscriptionsRaw)), nil
	})

	coursesListTool := mcp.NewTool(
		"Courses-List",
		mcp.WithDescription("List all courses of EDteam"),
		mcp.WithNumber("page", mcp.Description("Page number"), mcp.DefaultNumber(1)),
		mcp.WithNumber("limit", mcp.Description("Limit number of courses"), mcp.DefaultNumber(10)),
	)
	s.AddTool(coursesListTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		page, ok := request.Params.Arguments["page"].(float64)
		if !ok {
			page = 1
		}
		limit, ok := request.Params.Arguments["limit"].(float64)
		if !ok || limit <= 0 || limit > 10 {
			limit = 10
		}

		courses, err := GetCourses(ctx, uint(page), uint(limit))
		if err != nil {
			return nil, err
		}

		var coursesRaw []byte
		coursesRaw, err = json.Marshal(courses)
		if err != nil {
			return nil, err
		}

		// Create a response
		return mcp.NewToolResultText(string(coursesRaw)), nil
	})

	shoppingCartTool := mcp.NewTool(
		"Shopping-Cart-Add-Course",
		mcp.WithDescription("Add a course to your shopping cart"),
		mcp.WithNumber("course_id", mcp.Description("Course ID"), mcp.DefaultNumber(0), mcp.Required()),
	)
	s.AddTool(shoppingCartTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		courseID, ok := request.Params.Arguments["course_id"].(float64)
		if !ok {
			return nil, fmt.Errorf("course_id must be a number")
		}

		shoppingCart, err := AddCourseToShoppingCart(ctx, token, int(courseID))
		if err != nil {
			return nil, err
		}

		var shoppingCartRaw []byte
		shoppingCartRaw, err = json.Marshal(shoppingCart)
		if err != nil {
			return nil, err
		}

		// Create a response
		return mcp.NewToolResultText(string(shoppingCartRaw)), nil
	})

	if err := server.ServeStdio(s); err != nil {
		panic(err)
	}
}
