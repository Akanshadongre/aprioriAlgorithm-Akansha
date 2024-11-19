from flask import Flask, request, jsonify, render_template
from itertools import combinations, chain
from collections import defaultdict
import csv
import io

app = Flask(__name__)

def find_frequent_1_itemsets(transactions, min_support):
    item_count = defaultdict(int)
    for transaction in transactions:
        for item in transaction:
            item_count[frozenset([item])] += 1
    return {itemset for itemset, count in item_count.items() if count >= min_support}

def apriori_gen(frequent_itemsets, k):
    candidates = set()
    itemsets = list(frequent_itemsets)
    for i in range(len(itemsets)):
        for j in range(i + 1, len(itemsets)):
            l1, l2 = list(itemsets[i]), list(itemsets[j])
            # Join step: if the first k-2 items are equal, combine to form a k-itemset
            if l1[:k-2] == l2[:k-2] and l1[k-2] < l2[k-2]:
                candidate = frozenset(itemsets[i] | itemsets[j])
                if not has_infrequent_subset(candidate, frequent_itemsets):
                    candidates.add(candidate)
    return candidates

def has_infrequent_subset(candidate, frequent_itemsets):
    for subset in combinations(candidate, len(candidate) - 1):
        if frozenset(subset) not in frequent_itemsets:
            return True
    return False

def apriori(transactions, min_support):
    L = []
    k = 1
    Lk = find_frequent_1_itemsets(transactions, min_support)
    while Lk:
        L.append(Lk)
        Ck = apriori_gen(Lk, k + 1)
        item_count = defaultdict(int)
        for transaction in transactions:
            # Count candidates that appear in each transaction
            Ct = {candidate for candidate in Ck if candidate.issubset(transaction)}
            for candidate in Ct:
                item_count[candidate] += 1
        # Filter itemsets meeting min support
        Lk = {itemset for itemset, count in item_count.items() if count >= min_support}
        k += 1
    return set(chain.from_iterable(L))

# Route to display the HTML form
@app.route('/')
def index():
    return render_template('index.html')

# Route to process the uploaded CSV file
@app.route('/process_csv', methods=['POST'])
def process_csv():
    file = request.files['file']
    min_support = int(request.form['min_support'])
    
    # Parse CSV file
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    transactions = [row for row in csv_input]
    
    # Run Apriori algorithm
    frequent_itemsets = apriori(transactions, min_support)
    format_output(frequent_itemsets, args.input_file, min_support)

    print(f"Input file: {input_file}")
    print(f"Minimal support: {min_support}")
    formatted_output = "{{" + "}{".join(",".join(map(str, sorted(itemset))) for itemset in sorted(frequent_itemsets, key=lambda x: (len(x), x))) + "}}"
    print(formatted_output)
    print(f"End - total items: {len(frequent_itemsets)}")
    # result = [list(itemset) for itemset in result]
    return jsonify(result=formatted_output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
