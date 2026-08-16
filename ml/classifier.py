import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
from core.config import logger, MODEL_SAVE_PATH
from domain.text_cleaner import clean_text

class JobEmailClassifier:
    def __init__(self):
        self.model = None

    def train(self, df):
        """Trains the ML model on the provided DataFrame."""
        logger.info("Cleaning text for training...")
        df["clean_text"] = df["email_text"].apply(clean_text)

        X = df["clean_text"]
        y = df["label"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        logger.info("Building ML Pipeline...")
        self.model = Pipeline([
            ("tfidf", TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), min_df=1)),
            ("classifier", MultinomialNB())
        ])

        logger.info("Training Model...")
        self.model.fit(X_train, y_train)

        # Evaluation
        y_pred = self.model.predict(X_test)
        logger.info(f"Accuracy: {accuracy_score(y_test, y_pred):.2%}")
        logger.info(f"Precision: {precision_score(y_test, y_pred, zero_division=0):.2%}")
        logger.info(f"Recall: {recall_score(y_test, y_pred, zero_division=0):.2%}")
        logger.info(f"F1 Score: {f1_score(y_test, y_pred, zero_division=0):.2%}")
        logger.info("\nClassification Report:\n" + classification_report(
            y_test, y_pred, target_names=["Irrelevant Job", "Relevant Mobile/Flutter Job"], zero_division=0
        ))

    def save_model(self, path=MODEL_SAVE_PATH):
        if self.model:
            joblib.dump(self.model, path)
            logger.info(f"Model saved to {path}")
        else:
            logger.warning("No model to save.")

    def load_model(self, path=MODEL_SAVE_PATH):
        if os.path.exists(path):
            self.model = joblib.load(path)
            logger.info(f"Model loaded from {path}")
            return True
        return False

    def classify(self, email_text: str) -> dict:
        if not self.model:
            raise ValueError("Model not trained or loaded.")
        
        cleaned = clean_text(email_text)
        prediction = self.model.predict([cleaned])[0]
        probabilities = self.model.predict_proba([cleaned])[0]

        return {
            "is_relevant": bool(prediction),
            "irrelevant_probability": float(probabilities[0]),
            "relevant_probability": float(probabilities[1])
        }
