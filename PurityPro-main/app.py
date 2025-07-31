from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import io
import pandas as pd
import uuid
from sklearn.ensemble import IsolationForest

app = Flask(__name__)
CORS(app)

# Temporary buffer to store uploaded files
temp_buffer = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        # Store file in temporary buffer
        file_bytes = io.BytesIO()
        file.save(file_bytes)
        filename = f"{uuid.uuid4()}.csv"
        temp_buffer[filename] = file_bytes.getvalue()
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': 'File upload failed', 'details': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_file():
    try:
        filename = request.json['filename']
        if filename not in temp_buffer:
            return jsonify({'error': 'File not found in buffer'}), 404

        # Load the file from the temporary buffer
        file_bytes = temp_buffer[filename]
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            print(f"Data parsing error: {e}")
            return jsonify({'error': 'File processing failed', 'details': str(e)}), 500

        # Print columns before processing for debugging
        print("Original columns:", df.columns.tolist())

        # Strip whitespace from all columns
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Drop duplicates based on all columns
        df = df.drop_duplicates()

        # Apply mode imputation for categorical columns
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].notnull().any():  # Check if there's at least one non-null value
                df[col].fillna(df[col].mode()[0], inplace=True)

        # Apply mode imputation for numerical columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if df[col].isnull().any():  # Check if there are missing values
                df[col].fillna(df[col].mode()[0], inplace=True)

        # Apply Isolation Forest for outlier detection and handling
        for col in numeric_cols:
            if df[col].nunique() > 1:  # Ensure the column has enough unique values for modeling
                isolation_forest = IsolationForest(contamination=0.05, random_state=42)
                
                # Predict outliers (-1 for outliers, 1 for inliers)
                df['is_outlier'] = isolation_forest.fit_predict(df[[col]])

                # Debug: Print outlier counts and the first few predictions
                print(f"Outlier counts for {col}:", df['is_outlier'].value_counts().to_dict())
                print(f"First few outlier predictions for {col}:", df[['is_outlier', col]].head())

                # Calculate and print the median value for the column
                median_value = df[col].median()
                print(f"Median for {col}: {median_value}")  # Debug: Print the median value
                
                # Replace outliers (-1) with the median value
                df.loc[df['is_outlier'] == -1, col] = median_value
                
                # Drop the 'is_outlier' column after processing
                df.drop(columns=['is_outlier'], inplace=True)

        # Print columns after processing for debugging
        print("Processed columns:", df.columns.tolist())

        # Save the processed file to an in-memory bytes buffer
        processed_file = io.BytesIO()
        df.to_csv(processed_file, index=False)
        processed_file.seek(0)

        return send_file(
            processed_file,
            as_attachment=True,
            download_name='processed_file.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        print(f"Processing error: {e}")
        return jsonify({'error': 'File processing failed', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
