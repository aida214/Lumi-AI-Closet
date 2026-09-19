# ♡ Lumi AI Closet

### Your Digital Wardrobe & AI-Powered Personal Stylist

**Lumi AI Closet** is a modern digital wardrobe and AI styling application designed to make outfit planning easier, more personalized, and more fun.

Users can upload their clothing items, organize their wardrobe, create and save outfits, plan looks for the week, manage favorites, and interact with an AI styling assistant for personalized fashion suggestions.

---

## ✨ What is Lumi AI Closet?

Lumi AI Closet turns your physical wardrobe into a **digital closet**.

Instead of scrolling through your clothes wondering what to wear, you can keep your wardrobe organized in one place and use it to build outfits based on your personal style, occasion, season, and preferences.

The app combines:

**Digital Wardrobe + Outfit Builder + AI Stylist + Outfit Planner**

in one platform.

---

## 👗 Main Features

### 🧥 Digital Wardrobe

Upload and organize your clothing collection digitally.

Each wardrobe item can include:

* 📝 Clothing name
* 👗 Category
* 🎨 Color
* 🍂 Season
* 🏷️ Brand
* ✨ Style
* 🖼️ Clothing image

Your wardrobe becomes the foundation for creating personalized outfits.

---

### ✨ AI Personal Stylist

Get personalized fashion assistance through the AI stylist.

The assistant can help with:

* Outfit ideas
* Styling suggestions
* Color combinations
* Casual and formal looks
* Seasonal outfits
* Occasion-based styling
* Wardrobe-based recommendations
* Capsule wardrobe ideas
* Packing suggestions

Instead of giving generic fashion advice, Lumi is designed around **your digital wardrobe**.

---

### 👚 Outfit Builder

Create complete outfits by combining pieces from your wardrobe.

For example:

> Top + Jeans + Shoes + Bag + Accessories

Once you create a look, you can save it for later.

---

### 💗 Saved Looks

Save your favorite outfit combinations and access them whenever you need inspiration.

Each saved outfit can be connected to the individual wardrobe pieces used to create it.

---

### 📅 Weekly Outfit Planner

Plan what you're going to wear throughout the week.

Assign outfits to different days such as:

* Monday
* Tuesday
* Wednesday
* Thursday
* Friday
* Saturday
* Sunday

This helps reduce the everyday question:

> **"What should I wear today?"**

---

### ❤️ Favorites

Quickly save clothing pieces and looks that you use or love the most.

---

### 👤 Personal Accounts

Each user has their own account and personal wardrobe.

User-specific data is protected using **Supabase Authentication and Row Level Security (RLS)**.

---

## 🎀 Design

Lumi AI Closet is designed around a soft, modern fashion-app aesthetic.

The interface takes inspiration from:

* Pinterest
* Lemon8
* Korean fashion apps
* Apple-style interfaces
* Modern glassmorphism

### Visual Style

* 🌸 Soft pastel colors
* 💗 Baby pink and blush tones
* 🪞 Glassmorphism
* ✨ Rounded cards
* 🎀 Minimal layouts
* 🖼️ Image-focused wardrobe
* 📱 Responsive design
* ☁️ Soft gradients
* ♡ Gen-Z inspired UI

The goal is to make the app feel like a **modern fashion platform**, not a traditional database application.

---

## 🧠 How It Works

### 1. Create Your Wardrobe

Upload your clothing items and add information about each piece.

### 2. Organize Your Clothes

Filter and manage your wardrobe using categories such as color, season, and style.

### 3. Build an Outfit

Combine pieces from your wardrobe to create a complete look.

### 4. Save Your Look

Save outfits that you want to wear again.

### 5. Plan Your Week

Assign saved outfits to different days.

### 6. Ask Lumi

Use the AI stylist to get personalized fashion suggestions and outfit ideas.

---

## 🗄️ Database

Lumi AI Closet uses **Supabase** for its backend infrastructure.

The application uses tables for:

* User profiles
* Wardrobe items
* Saved outfits
* Outfit items
* Weekly planner
* Favorites
* Chat history

### Outfit Relationships

Saved outfits are connected to wardrobe pieces through the `outfit_items` junction table.

This allows one saved outfit to contain multiple clothing items while keeping the wardrobe organized separately.

---

## 🔐 Security

Lumi AI Closet uses **Row Level Security (RLS)** to protect user data.

Users can access their own:

* Wardrobe
* Saved outfits
* Planner
* Favorites
* Profile information
* Relevant chat history

Supabase credentials are stored outside the source code using Streamlit secrets.

Sensitive credentials should never be committed to the repository.

---

## 🛠️ Tech Stack

| Technology          | Use                     |
| ------------------- | ----------------------- |
| 🐍 Python           | Application development |
| 🎈 Streamlit        | Web application         |
| 🗄️ Supabase        | Backend & database      |
| 🐘 PostgreSQL       | Relational database     |
| 🔐 Supabase Auth    | User authentication     |
| ☁️ Supabase Storage | Image storage           |
| 🤖 OpenAI           | AI styling features     |
| 📊 Pandas           | Data processing         |
| 🐙 Git & GitHub     | Version control         |

---

## 📂 Project Structure

```text
Lumi-AI-Closet/
│
├── app.py
├── supabaseclient.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── pages/
│   ├── dashboard.py
│   ├── wardrobe.py
│   └── ...
│
├── modules/
│   ├── ...
│   └── ...
│
└── .streamlit/
    └── secrets.toml
```

`secrets.toml` contains private configuration and should remain excluded from GitHub.

---

## 🚀 Project Goals

Lumi AI Closet was created to explore how **AI and modern application development can solve a simple everyday problem: deciding what to wear.**

The project combines:

* AI
* Data management
* Database design
* Authentication
* Image handling
* Personalization
* Fashion recommendation
* UI/UX design

into one application.

---

## 📚 What This Project Demonstrates

This project demonstrates practical experience with:

* Python development
* Streamlit
* Supabase
* PostgreSQL
* Authentication
* Row Level Security
* CRUD operations
* Relational database design
* API integration
* AI-powered applications
* Image/file handling
* Git & GitHub
* UI/UX development
* Debugging and application architecture

---

## 🔮 Future Ideas

Lumi AI Closet can be expanded with:

* 🤖 Automatic clothing recognition
* 🎨 Automatic color detection
* 🌦️ Weather-based outfit recommendations
* 🧳 AI packing assistant
* 👚 Capsule wardrobe generator
* 📊 Wardrobe analytics
* 🔄 Outfit rotation tracking
* 🛍️ Personalized shopping suggestions
* 🖼️ AI-generated outfit previews
* 📱 Improved mobile experience
* 🧠 More advanced personalized recommendations

---

## 👩‍💻 Developer

### Aiyda Syed

**BS Data Science Student**

Interested in:

`Data Science` · `Data Analytics` · `Machine Learning` · `Artificial Intelligence` · `Python`

---

## 🚧 Project Status

**Active Development**

Lumi AI Closet is an ongoing project. New features, styling capabilities, database improvements, and UI enhancements are continuously being developed.

---

### ♡ Lumi AI Closet

**Your wardrobe. Your style. Your AI stylist.**

