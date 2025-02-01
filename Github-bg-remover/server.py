from flask import Flask, request, jsonify
import database

app = Flask(__name__)

@app.route('/log-ad-view', methods=['POST'])
def log_ad_view():
    """
    Log ad views (optional for analytics or tracking).
    """
    try:
        # Extract data from the request
        data = request.json
        user_id = data.get('user_id')
        ad_id = data.get('ad_id')  # Optional: Track which ad was viewed

        # Log the ad view (optional)
        print(f"User {user_id} viewed ad {ad_id}")

        # You can also update your database or perform other actions here
        # Example: database.log_ad_view(user_id, ad_id)

        return jsonify(success=True), 200

    except Exception as e:
        print(f"Error logging ad view: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)