# FAQ Chatbot (TF-IDF & Cosine Similarity)

A beginner-friendly, modular FAQ Chatbot built with Python, Natural Language Processing (NLP) using NLTK and scikit-learn, and a modern ChatGPT-inspired desktop graphical user interface using Tkinter.

---

## 📁 Project Structure

```
FAQ_Chatbot/
├── data/
│   └── faqs.csv           # FAQ dataset (Questions & Answers)
├── chatbot.py             # FAQ matching engine & TF-IDF logic
├── preprocessing.py       # NLP text cleaning, tokenization & stopwords
├── gui.py                 # Tkinter ChatGPT-style desktop UI
├── test_chatbot.py        # Automated test suite
├── requirements.txt       # Dependencies
└── README.md              # Project documentation
```

---

## ⚙️ How the Components Interact

1. **`preprocessing.py`**:
   - Cleans incoming text (lowercasing, punctuation removal, whitespace normalization).
   - Tokenizes text using NLTK's `word_tokenize`.
   - Strips English stopwords (`stopwords.words('english')`).
   - Returns clean normalized text ready for vectorization.

2. **`chatbot.py`**:
   - **Load Dataset Once**: Reads `data/faqs.csv` and validates `Question` and `Answer` columns.
   - **TF-IDF Vectorizer**: Fits `TfidfVectorizer` on preprocessed FAQ questions at startup and creates a vector matrix.
   - **Matching Engine**: Transforms the user's question with the existing vectorizer, calculates `cosine_similarity` against all stored FAQ vectors, and selects the highest score.
   - **Threshold Logic**: If `similarity_score >= 0.30`, returns the matched answer; otherwise returns a fallback message: *"Sorry, I couldn't find a relevant answer to that question."*

3. **`gui.py`**:
   - ChatGPT-inspired dark desktop chat interface created with pure Tkinter.
   - Distinct message cards for User and Assistant.
   - Responsive scrolling, Enter key binding, Send button, and Clear Chat functionality.
   - Separates UI display from chatbot matching logic.

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- `pip` package manager

### 2. Install Required Dependencies
Run the following command in the project directory:

```bash
pip install -r requirements.txt
```

### 3. NLTK Data Setup
The application automatically checks and downloads the required NLTK resources (`punkt`, `punkt_tab`, `stopwords`) on first run. 

If you prefer to download them manually:
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords')"
```

---

## 🖥️ How to Run

### Option 1: Desktop Chat GUI (ChatGPT-style Interface)
To launch the modern desktop chat interface:
```bash
python gui.py
```

### Option 2: Terminal / Command Line Interface
To run the interactive CLI in the terminal:
```bash
python chatbot.py
```

### Option 3: Run Automated Tests
To run the validation test suite:
```bash
python test_chatbot.py
```

---

## 🎯 How the Similarity Threshold Works

Cosine similarity measures the angle between the user query vector $\vec{u}$ and an FAQ question vector $\vec{v}$:

$$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$$

- **Range:** Values range from `0.0` (no word overlap / completely unrelated) to `1.0` (exact match).
- **Default Threshold:** Set to `0.30` (`DEFAULT_SIMILARITY_THRESHOLD = 0.30` in `chatbot.py`).
- **Behavior:**
  - `score >= 0.30`: Confident match found $\rightarrow$ Returns the FAQ answer.
  - `score < 0.30`: Unrelated query $\rightarrow$ Returns *"Sorry, I couldn't find a relevant answer to that question."*

You can adjust the threshold by modifying the `DEFAULT_SIMILARITY_THRESHOLD` constant in `chatbot.py`.

---

## 📊 Dataset Format

The dataset should be a CSV file with at least two columns: `Question` and `Answer`.

Example:
```csv
Question,Answer
"How do I apply for undergraduate admissions?","Apply through the GIKI Admissions Portal at https://admissions.giki.edu.pk."
"What is the location of GIKI?","GIKI is located near Tarbela Dam in Khyber Pakhtunkhwa, about a 1.5-hour drive from Islamabad."
```
