from flask import Flask, render_template, request
import pickle
import pandas as pd
import numpy as np

popular_df = pickle.load(open('popular.pkl','rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similar = pickle.load(open('similar.pkl','rb'))
final_ratings = pickle.load(open('FR.pkl','rb'))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_ratings'].values),
                           available=list(popular_df['Availability'].values)
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['post'])
def recommend_books():
    user_input = request.form.get('user_input', '').strip()
    if not user_input:
        return render_template('recommend.html', data=None, message="Please enter a book title")

    # Case-insensitive partial match for book titles
    matching_books = final_ratings[
        final_ratings['Book-Title'].str.contains(user_input, case=False, na=False)
    ]

    if matching_books.empty:
        return render_template('recommend.html', data=None, message=f"No books found containing the word: '{user_input}'")

    # detect a plausible availability column name in the dataframe
    availability_col = None
    for candidate in ['Availability', 'available', 'Available', 'availability',
                      'link', 'url', 'URL', 'Available-URL', 'available_link']:
        if candidate in matching_books.columns:
            availability_col = candidate
            break

    # Group by Book-Title, Book-Author, Image and compute mean rating; also pull first availability if present
    if availability_col:
        grouped = (
            matching_books
            .groupby(['Book-Title', 'Book-Author', 'Image-URL-M'], as_index=False)
            .agg({ 'Book-Rating': 'mean', availability_col: 'first' })
        )
        # Normalize column name for template usage
        grouped = grouped.rename(columns={availability_col: 'Availability'})
    else:
        grouped = (
            matching_books
            .groupby(['Book-Title', 'Book-Author', 'Image-URL-M'], as_index=False)
            .agg({ 'Book-Rating': 'mean' })
        )
        grouped['Availability'] = '#'

    # Sort and take top 50
    grouped = grouped.sort_values(by='Book-Rating', ascending=False).head(50)

    # Prepare the final result: include availability as 5th element
    data = []
    for _, row in grouped.iterrows():
        avail = row.get('Availability', '#')
        # if availability looks like NaN, replace with '#'
        if pd.isna(avail):
            avail = '#'
        data.append([
            row['Book-Title'],
            row['Book-Author'],
            row['Image-URL-M'],
            round(row['Book-Rating'], 2),
            avail
        ])

    return render_template('recommend.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)