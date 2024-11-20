from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import time
import csv
from collections import defaultdict, Counter
from itertools import combinations

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # For session management

# Your existing functions like load_transactions, apriori, etc.

@app.route('/')
def index():
    return render_template('index.html')  # Create an index.html for the form

@app.route('/run_apriori', methods=['POST'])
def run_apriori():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    min_support = int(request.form.get('min_support', 1))

    file_path = f"./uploads/{file.filename}"
    file.save(file_path)

    try:
        transactions = load_transactions(file_path)
        start_time = time.time()
        frequent_itemsets = apriori(transactions, min_support)
        maximal_frequent_itemsets = get_maximal_frequent_itemsets(frequent_itemsets)
        maximal_frequent_itemsets.sort(key=lambda x: (len(x), x))

        # Format the itemsets as per your required output
        formatted_itemsets = [f"{{{','.join(map(str, itemset))}}}" for itemset in maximal_frequent_itemsets]
        end_time = time.time()

        result = {
            "Input file": file.filename,
            "Minimal support": min_support,
            "Maximal frequent itemsets": f"{{{','.join(formatted_itemsets)}}}",
            "End - total items": len(maximal_frequent_itemsets),
            "Total running time": f"{end_time - start_time:.6f} seconds"
        }

        # Store result in session
        session['result'] = result

        # Redirect to the result page
        return redirect(url_for('result'))  # This will redirect to the result page

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/result')
def result():
    # Check if result is stored in the session
    if 'result' not in session:
        return redirect(url_for('index'))  # Redirect to index if no result is found

    result = session['result']  # Get the result from session
    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
