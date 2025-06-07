# Social Media Sentiment Analysis and Classification

This is a team project that aims to classify sentiments of social media posts into three categories — positive, neutral, and negative.

## Dataset
The dataset is sourced from Kaggle: [Social Media Sentiments Analysis Dataset](https://www.kaggle.com/datasets/kashishparmar02/social-media-sentiments-analysis-dataset)

Added data sources: [Twitter Tweets Sentiment Dataset](https://www.kaggle.com/datasets/yasserh/twitter-tweets-sentiment-dataset), [Sentiment Analysis](https://www.kaggle.com/datasets/mdismielhossenabir/sentiment-analysis)


## Goals
- Explore and analyze the data
- Preprocess the data
- Train classifier models: Random Forest, Logistic Regression, Naive Bayes, Neural network, and fine-tuned pretrained ModernBERT
- Evaluate and compare the models' preformances
- Locally executable user interface connected to Mastodon API - in the UI, you can compare the original and preprocessed text and models classification results for both texts, and also make correction which are stored to the separate CSV file.

## Requirements
Make sure that you have Python3 and nltk modul installed

## Fine-tuned pretrained ModernBERT model 
The model is available here: https://drive.google.com/drive/folders/19qKtlwidhl-nzZBKNNWZmhfnF6R49ToO?usp=sharing

Download the model and unzip it to the same folder with app.py.

Run the application in terminal, using command python3 app.py
