# Second-Hand Vehicle Buying and Selling System

## Overview

This project is a web application developed using **Python Flask**, **HTML**, and **MySQL**. It allows users to buy and sell second-hand vehicles, with features tailored for creating advertisements, managing offers, handling payments, and initiating conversations. The application employs raw SQL queries for database interactions, ensuring efficient and direct data manipulation.

---

## Features

### Common Functionalities
1. **Login and Register System:**
   - Supports different user types (e.g., buyers, sellers, admin).
   - Provides a secure authentication mechanism.

2. **Custom Functional Requirement:**
   - A feature introduced based on project requirements, reviewed, and approved by the course TA.

### Topic-Specific Functionalities

#### 1. **Creating an Ad for a Vehicle**
   - Users can select a vehicle type (Car, Motorcycle, or Van).
   - Fill in detailed information such as make, model, year, price, and condition.
   - Upload at least one image for the ad (quality checks included).
   - Attach an expert report in PDF format for the vehicle.

#### 2. **Making Offers for an Ad**
   - Advanced filters to search for specific ads based on criteria like price range, type, location, etc.
   - List all available ads.
   - Make an offer on a selected ad.
   - The seller can accept or reject the offer.
   - Upon acceptance:
     - Users enter payment details.
     - The system verifies the buyer's balance.
     - Deducts the amount and processes the payment.
     - Updates the transaction status and removes the ad from availability.

#### 3. **Initiating Conversations with Sellers**
   - Search for ads using filters.
   - View detailed ad listings.
   - Start a direct conversation with the seller to ask questions or clarify details.

#### 4. **Additional Functionalities**
   - **Rating and Commenting:** Buyers can rate and leave comments for attended classes or experiences with sellers.
   - **Class Creation (if applicable):** Coaches or sellers can create specialized offers or classes and publish them with constraints.

---

## Technology Stack

- **Backend:** Python Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **SQL Queries:** Raw SQL queries for database interactions
- **Deployment:** Docker

---

## Installation and Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Build and Run the Docker Container:**
   - Ensure Docker is installed and running on your system.
   - Build the Docker image:
     ```bash
     docker build -t vehicle-marketplace .
     ```
   - Run the Docker container:
     ```bash
     docker run -d -p 5000:5000 vehicle-marketplace
     ```

3. **Access the Website:**
   - Open a browser and navigate to `http://localhost:5000`.

---

## Usage

### User Registration and Login
- New users can register with their details.
- Existing users log in to access features based on their roles (buyer/seller/admin).

### Creating an Ad
1. Navigate to the "Create Ad" section.
2. Fill in vehicle details, upload images, and attach a PDF expert report.
3. Submit the ad for publishing.

### Searching and Making Offers
1. Use the search bar or advanced filters to find ads.
2. View ad details and click "Make Offer."
3. Enter your offer amount and confirm.

### Conversation with Seller
1. Select an ad and click "Message Seller."
2. Start a conversation to ask questions or negotiate details.

### Admin Panel
- Manage users, ads, and transactions.


## File Structure

```plaintext
project-directory/
  |-- app.py            # Main Flask application
  |-- templates/        # HTML templates
  |-- static/           # CSS, JS, and images
  |-- database.sql      # SQL schema
  |-- requirements.txt  # Dependencies
  |-- Dockerfile        # Docker configuration
  |-- README.md         # Documentation
```

---

## Future Enhancements

- **Payment Gateway Integration:** Support for online payments.
- **Advanced Analytics:** Insights into user activity and sales trends.
- **Mobile Compatibility:** Responsive design for mobile users.

---

## Authors
- Names: [Your Names]
- IDs: [Your IDs]
- Course: CS353 - Fall 2024-2025

---

## License
This project is developed as part of the CS353 course and is intended for educational purposes.

