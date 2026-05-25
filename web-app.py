from flask import Flask, render_template, request, redirect, url_for, session
import MySQLdb
import pickle
import numpy as np
import re


# Load pickled dataframes and other resources
popular_df = pickle.load(open('popular1.pkl','rb'))
happy_df = pickle.load(open('happy.pkl', 'rb'))
sad_df = pickle.load(open('sad.pkl', 'rb'))
relaxed_df = pickle.load(open('relaxed.pkl', 'rb'))
excited_df = pickle.load(open('excited.pkl', 'rb'))
thoughtful_df = pickle.load(open('thoughtful.pkl', 'rb'))
curious_df = pickle.load(open('curious.pkl', 'rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_score = pickle.load(open('similarity_scores1.pkl','rb'))
bestbooks = pickle.load(open('bestbooks.pkl','rb'))
preview_books = pickle.load(open('preview.pkl','rb'))

app = Flask(__name__)
app.secret_key = '****'  # Replace with your actual secret key

# Database configuration
db_config = {
    'host': 'localhost',       # Your MySQL server address
    'user': 'root',            # Your MySQL username
    'password': '****',       # Your MySQL password
    'database': 'readmate_db'  # Your database name
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/books')
def books_page():
    return render_template('books.html',
                           book_name=popular_df['book-title'].values[:100].tolist(),
                           author=popular_df['author'].values[:100].tolist(),
                           images=popular_df['coverImg'].values[:100].tolist(),
                           avg_rating=popular_df['avg_rating'].values[:100].tolist(),
                           liked=popular_df['likedPercent'].values[:100].tolist(),
                           description=popular_df['description'].values[:100].tolist(),
                           series=popular_df['series'].values[:100].tolist(),
                           language=popular_df['language'].values[:100].tolist(),
                           genres=popular_df['genres'].values[:100].tolist(),
                           characters=popular_df['characters'].values[:100].tolist(),
                           book_format=popular_df['bookFormat'].values[:100].tolist(),
                           edition=popular_df['edition'].values[:100].tolist(),
                           pages=popular_df['pages'].values[:100].tolist(),
                           publisher=popular_df['publisher'].values[:100].tolist(),
                           publish_date=popular_df['publishDate'].values[:100].tolist(),
                           awards=popular_df['awards'].values[:100].tolist(),
                           num_ratings=popular_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=popular_df['ratingsByStars'].values[:100].tolist(),
                           setting=popular_df['setting'].values[:100].tolist()
                           )

@app.route('/mood')
def mood():
    return render_template('mood.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']

        # Connect to the database
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        # Query to check if the user exists
        cursor.execute("SELECT password FROM users WHERE gmail = %s", (gmail,))
        result = cursor.fetchone()

        if result and result[0] == password:  # Compare with plain password (use hashed password in production)
            session['gmail'] = gmail
            return redirect(url_for('books_page'))
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']

        # Connect to the database
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        try:
            # Insert new user into the database
            cursor.execute("INSERT INTO users (gmail, password) VALUES (%s, %s)", (gmail, password))
            db.commit()
            return redirect(url_for('login'))  # Redirect to login page after successful registration
        except MySQLdb.Error as e:
            print(f"Error: {e}")
            db.rollback()  # Rollback in case of error
            return "Registration failed. Please try again."

        finally:
            cursor.close()
            db.close()

    return render_template('register.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        book_name = request.form.get('book_name')

        # Check if the book exists in the dataset
        if book_name in pt.index:
            # Get the index of the book
            index = np.where(pt.index == book_name)[0][0]
            # Fetch the similar items based on similarity score
            similar_items = sorted(list(enumerate(similarity_score[index])), key=lambda x: x[1], reverse=True)[1:6]

            # Prepare data including the searched book
            data = []

            # Add the searched book to the result
            temp_df = bestbooks[bestbooks['book-title'] == book_name]
            searched_book = []
            searched_book.extend(temp_df.drop_duplicates('book-title')['book-title'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['author'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['coverImg'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['rating'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['likedPercent'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['description'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['series'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['language'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['genres'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['characters'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['bookFormat'].values.tolist())
            #searched_book.extend(temp_df.drop_duplicates('book-title')['edition'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['pages'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['publishDate'].values.tolist())
            #searched_book.extend(temp_df.drop_duplicates('book-title')['awards'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['numRatings'].values.tolist())
            #searched_book.extend(temp_df.drop_duplicates('book-title')['ratingsByStars'].values.tolist())
            searched_book.extend(temp_df.drop_duplicates('book-title')['setting'].values.tolist())
            data.append(searched_book)

            # Add similar items to the result
            for i in similar_items:
                temp_df = bestbooks[bestbooks['book-title'] == pt.index[i[0]]].drop_duplicates('book-title')

                if temp_df.empty or temp_df['book-title'].isna().any():
                    continue  # Skip if book title is missing
                item = []
                item.extend(temp_df.drop_duplicates('book-title')['book-title'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['author'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['coverImg'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['rating'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['likedPercent'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['description'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['series'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['language'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['genres'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['characters'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['bookFormat'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['pages'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['publishDate'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['numRatings'].values.tolist())
                item.extend(temp_df.drop_duplicates('book-title')['setting'].values.tolist())

                data.append(item)

            return render_template('search.html', data=data, book_name=book_name)

        else:
            # If the book is not found, search by author or return "not found" message
            temp_df = bestbooks[bestbooks['author'].notna() & bestbooks['author'].str.contains(book_name, case=False)]

            if not temp_df.empty:
                data = []
                for _, row in temp_df.iterrows():
                    item = [row['book-title'], row['author'], row['coverImg'], row['rating'],row['likedPercent'],row['description'],row['series'],row['language'],row['genres'],row['characters'],row['bookFormat'],row['pages'],row['publishDate'],row['numRatings'],row['setting']]
                    data.append(item)
                return render_template('search.html', data=data)
            else:
                return render_template('search.html', data=None)

    return redirect(url_for('books_page'))




@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']

        # Connect to the database
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        # Query to check if the admin user exists
        cursor.execute("SELECT password FROM admin_users WHERE gmail= %s", (gmail,))
        result = cursor.fetchone()

        if result and result[0] == password:  # Compare with plain password (use hashed password in production)
            session['username'] = gmail
            return redirect(url_for('feedbackdisplay'))  # Redirect to feedback page (you need to implement this route)
        else:
            return "Invalid credentials", 401

    return render_template('adminlogin.html')  # Render admin login page

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        # Retrieve data from form
        name = request.form['name']
        email = request.form['email']
        feedback_text = request.form['feedback']

        # Connect to the database
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        # Insert feedback into the feedback table
        cursor.execute("""
            INSERT INTO feedback (name, email, feedback)
            VALUES (%s, %s, %s)
        """, (name, email, feedback_text))

        # Commit changes and close the connection
        db.commit()
        cursor.close()
        db.close()



    return render_template('feedback.html')

@app.route('/feedbackdisplay')
def feedbackdisplay():
    # Connect to the database
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()

    # Query to fetch feedback from the feedback table
    cursor.execute("SELECT id, name, email, feedback FROM feedback")
    feedback_list = cursor.fetchall()

    # Close the cursor and database connection
    cursor.close()
    db.close()

    # Render the feedback page with the fetched data
    return render_template('feedbackdisplay.html', feedback_list=feedback_list)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/happy')
def happy():
    return render_template('happy.html',
                           rating =happy_df['rating'].values[:100].tolist(),
                           book_name=happy_df['book-title'].values[:100].tolist(),
                           author=happy_df['book-author'].values[:100].tolist(),
                           images=happy_df['coverImg'].values[:100].tolist(),
                           year=happy_df['year-of-publication'].values[:100].tolist(),
                           liked=happy_df['likedPercent'].values[:100].tolist(),
                           description=happy_df['description'].values[:100].tolist(),
                           series=happy_df['series'].values[:100].tolist(),
                           language=happy_df['language'].values[:100].tolist(),
                           genres=happy_df['genres'].values[:100].tolist(),
                           characters=happy_df['characters'].values[:100].tolist(),
                           book_format=happy_df['bookFormat'].values[:100].tolist(),
                           edition=happy_df['edition'].values[:100].tolist(),
                           pages=happy_df['pages'].values[:100].tolist(),
                           publisher=happy_df['publisher_x'].values[:100].tolist(),
                           publish_date=happy_df['publishDate'].values[:100].tolist(),
                           awards=happy_df['awards'].values[:100].tolist(),
                           num_ratings=happy_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=happy_df['ratingsByStars'].values[:100].tolist(),
                           setting=happy_df['setting'].values[:100].tolist()
                           )

@app.route('/sad')
def sad():
    return render_template('sad.html',
                           book_name=sad_df['book-title'].values[:100].tolist(),
                           author=sad_df['book-author'].values[:100].tolist(),
                           images=sad_df['coverImg'].values[:100].tolist(),
                           year=sad_df['year-of-publication'].values[:100].tolist(),
                           liked=sad_df['likedPercent'].values[:100].tolist(),
                           description=sad_df['description'].values[:100].tolist(),
                           series=sad_df['series'].values[:100].tolist(),
                           language=sad_df['language'].values[:100].tolist(),
                           genres=sad_df['genres'].values[:100].tolist(),
                           characters=sad_df['characters'].values[:100].tolist(),
                           book_format=sad_df['bookFormat'].values[:100].tolist(),
                           edition=sad_df['edition'].values[:100].tolist(),
                           pages=sad_df['pages'].values[:100].tolist(),
                           publisher=sad_df['publisher_x'].values[:100].tolist(),
                           publish_date=sad_df['publishDate'].values[:100].tolist(),
                           awards=sad_df['awards'].values[:100].tolist(),
                           num_ratings=sad_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=sad_df['ratingsByStars'].values[:100].tolist(),
                           setting=sad_df['setting'].values[:100].tolist()
                           )

@app.route('/relaxed')
def relaxed():
    return render_template('relaxed.html',
                           book_name=relaxed_df['book-title'].values[:100].tolist(),
                           author=relaxed_df['book-author'].values[:100].tolist(),
                           images=relaxed_df['coverImg'].values[:100].tolist(),
                           year=relaxed_df['year-of-publication'].values[:100].tolist(),
                           liked=relaxed_df['likedPercent'].values[:100].tolist(),
                           description=relaxed_df['description'].values[:100].tolist(),
                           series=relaxed_df['series'].values[:100].tolist(),
                           language=relaxed_df['language'].values[:100].tolist(),
                           genres=relaxed_df['genres'].values[:100].tolist(),
                           characters=relaxed_df['characters'].values[:100].tolist(),
                           book_format=relaxed_df['bookFormat'].values[:100].tolist(),
                           edition=relaxed_df['edition'].values[:100].tolist(),
                           pages=relaxed_df['pages'].values[:100].tolist(),
                           publisher=relaxed_df['publisher_x'].values[:100].tolist(),
                           publish_date=relaxed_df['publishDate'].values[:100].tolist(),
                           awards=relaxed_df['awards'].values[:100].tolist(),
                           num_ratings=relaxed_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=relaxed_df['ratingsByStars'].values[:100].tolist(),
                           setting=relaxed_df['setting'].values[:100].tolist()
                           )

@app.route('/excited')
def excited():
    return render_template('excited.html',
                           book_name=excited_df['book-title'].values[:100].tolist(),
                           author=excited_df['book-author'].values[:100].tolist(),
                           images=excited_df['coverImg'].values[:100].tolist(),
                           year=excited_df['year-of-publication'].values[:100].tolist(),
                           liked=excited_df['likedPercent'].values[:100].tolist(),
                           description = excited_df['description'].values[:100].tolist(),
                           series=excited_df['series'].values[:100].tolist(),
                           language=excited_df['language'].values[:100].tolist(),
                           genres=excited_df['genres'].values[:100].tolist(),
                           characters=excited_df['characters'].values[:100].tolist(),
                           book_format=excited_df['bookFormat'].values[:100].tolist(),
                           edition=excited_df['edition'].values[:100].tolist(),
                           pages=excited_df['pages'].values[:100].tolist(),
                           publisher=excited_df['publisher_x'].values[:100].tolist(),
                           publish_date=excited_df['publishDate'].values[:100].tolist(),
                           awards=excited_df['awards'].values[:100].tolist(),
                           num_ratings=excited_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=excited_df['ratingsByStars'].values[:100].tolist(),
                           setting=excited_df['setting'].values[:100].tolist()
                           )

@app.route('/thoughtful')
def thoughtful():
    return render_template('thoughtful.html',
                           book_name=thoughtful_df['book-title'].values[:100].tolist(),
                           author=thoughtful_df['book-author'].values[:100].tolist(),
                           images=thoughtful_df['coverImg'].values[:100].tolist(),
                           year=thoughtful_df['year-of-publication'].values[:100].tolist(),
                           liked=thoughtful_df['likedPercent'].values[:100].tolist(),
                           description=thoughtful_df['description'].values[:100].tolist(),
                           series=thoughtful_df['series'].values[:100].tolist(),
                           language=thoughtful_df['language'].values[:100].tolist(),
                           genres=thoughtful_df['genres'].values[:100].tolist(),
                           characters=thoughtful_df['characters'].values[:100].tolist(),
                           book_format=thoughtful_df['bookFormat'].values[:100].tolist(),
                           edition=thoughtful_df['edition'].values[:100].tolist(),
                           pages=thoughtful_df['pages'].values[:100].tolist(),
                           publisher=thoughtful_df['publisher_x'].values[:100].tolist(),
                           publish_date=thoughtful_df['publishDate'].values[:100].tolist(),
                           awards=thoughtful_df['awards'].values[:100].tolist(),
                           num_ratings=thoughtful_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=thoughtful_df['ratingsByStars'].values[:100].tolist(),
                           setting=thoughtful_df['setting'].values[:100].tolist()
                           )

@app.route('/curious')
def curious():
    return render_template('curious.html',
                           book_name=curious_df['book-title'].values[:100].tolist(),
                           author=curious_df['book-author'].values[:100].tolist(),
                           images=curious_df['coverImg'].values[:100].tolist(),
                           year=curious_df['year-of-publication'].values[:100].tolist(),
                           liked=curious_df['likedPercent'].values[:100].tolist(),
                           description=curious_df['description'].values[:100].tolist(),
                           series=curious_df['series'].values[:100].tolist(),
                           language=curious_df['language'].values[:100].tolist(),
                           genres=curious_df['genres'].values[:100].tolist(),
                           characters=curious_df['characters'].values[:100].tolist(),
                           book_format=curious_df['bookFormat'].values[:100].tolist(),
                           edition=curious_df['edition'].values[:100].tolist(),
                           pages=curious_df['pages'].values[:100].tolist(),
                           publisher=curious_df['publisher_x'].values[:100].tolist(),
                           publish_date=curious_df['publishDate'].values[:100].tolist(),
                           awards=curious_df['awards'].values[:100].tolist(),
                           num_ratings=curious_df['numRatings'].values[:100].tolist(),
                           ratings_by_stars=curious_df['ratingsByStars'].values[:100].tolist(),
                           setting=curious_df['setting'].values[:100].tolist()
                           )
@app.route('/preview')
def preview():
    return render_template('preview.html',
                           book_name=preview_books['book-title'].values[:100].tolist(),
                           rating=preview_books['rating'].values[:100].tolist(),
                           author=preview_books['author'].values[:100].tolist(),
                           images=preview_books['coverImg'].values[:100].tolist(),
                           liked=preview_books['likedPercent'].values[:100].tolist(),
                           description=preview_books['description'].values[:100].tolist(),
                           series=preview_books['series'].values[:100].tolist(),
                           language=preview_books['language'].values[:100].tolist(),
                           genres=preview_books['genres'].values[:100].tolist(),
                           characters=preview_books['characters'].values[:100].tolist(),
                           book_format=preview_books['bookFormat'].values[:100].tolist(),
                           edition=preview_books['edition'].values[:100].tolist(),
                           pages=preview_books['pages'].values[:100].tolist(),
                           publisher=preview_books['publisher'].values[:100].tolist(),
                           publish_date=preview_books['publishDate'].values[:100].tolist(),
                           awards=preview_books['awards'].values[:100].tolist(),
                           num_ratings=preview_books['numRatings'].values[:100].tolist(),
                           ratings_by_stars=preview_books['ratingsByStars'].values[:100].tolist(),
                           setting=preview_books['setting'].values[:100].tolist(),
                           link=preview_books['link'].values[:100].tolist()
                           )


if __name__ == '__main__':
    app.run(debug=True)
