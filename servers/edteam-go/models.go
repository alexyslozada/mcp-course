package main

import (
	"time"
)

type Subscription struct {
	ID               int       `json:"id"`
	SubscriptionDate time.Time `json:"subscription_date"`
	Months           int       `json:"months"`
	BeginsAt         time.Time `json:"begins_at"`
	EndsAt           time.Time `json:"ends_at"`
	State            string    `json:"state"`
	Observations     string    `json:"observations"`
	CreatedAt        time.Time `json:"created_at"`
	Buyer            string    `json:"buyer"`
}

type SubscriptionResponse struct {
	Data []Subscription `json:"data"`
}

type Login struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type LoginResponse struct {
	Data struct {
		Token string `json:"token"`
	} `json:"data"`
}

type CourseResponse struct {
	Data []struct {
		Course struct {
			AddressedTo     string    `json:"addressed_to"`
			CourseType      string    `json:"course_type"`
			CreatedAt       time.Time `json:"created_at"`
			ID              int       `json:"id"`
			Level           string    `json:"level"`
			Name            string    `json:"name"`
			OnSale          bool      `json:"on_sale"`
			Picture         string    `json:"picture"`
			Slug            string    `json:"slug"`
			Subtitle        string    `json:"subtitle"`
			VerticalPicture string    `json:"vertical_picture"`
			Visible         bool      `json:"visible"`
			YouLearn        string    `json:"you_learn"`
		} `json:"course"`
		CoursePrices []struct {
			BasePrice  int       `json:"base_price"`
			CreatedAt  time.Time `json:"created_at"`
			CurrencyId int       `json:"currency_id"`
			ID         int       `json:"id"`
			Price      int       `json:"price"`
		} `json:"course_prices"`
		Professors []struct {
			Biography   string    `json:"biography"`
			City        string    `json:"city"`
			CountryName string    `json:"country_name"`
			CreatedAt   time.Time `json:"created_at"`
			Firstname   string    `json:"firstname"`
			ID          int       `json:"id"`
			Lastname    string    `json:"lastname"`
			Nickname    string    `json:"nickname"`
			Picture     string    `json:"picture"`
		} `json:"professors"`
	} `json:"data"`
}

type ShoppingCartResponse struct {
	Messages []struct {
		Title   string `json:"title"`
		Message string `json:"message"`
		Code    string `json:"code"`
	}
}
