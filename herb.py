from flask.views import MethodView
from flask_smorest import Blueprint
import csv

blp = Blueprint("herbs", __name__, description="Operations on herbs")

# GET request: Fetching data from CSV file
@blp.route("/herbs")  
class HerbList(MethodView):
    
    def get(self):
        herbs = []
        with open('herbs_data.csv', mode='r') as file:  # Open your CSV file
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                herbs.append({
                    "name": row.get("Herb name"),  # Match CSV column name
                    "scientific_name": row.get("Scientific Name"),  # Match CSV column name
                    "medicinal_properties": row.get("Medicinal properties"),  # Match CSV column name
                    "usage": row.get("Usage"),  # Match CSV column name
                    "side_effects": row.get("Side effects"),  # Match CSV column name
                    "region_origin": row.get("Region/Origin")  # Match CSV column name
                })
        return herbs, 200  # Return the herbs list

    # POST request: Adding data from the client
    def post(self):
        from flask import request
        data = request.get_json()
        # For now, you could append to CSV or directly return the data received
        return {"message": "Herb added", "data": data}, 201
@blp.route("/herbs/<string:herb_name>")  # Use herb_name as the identifier
class Herb(MethodView):
    
    def put(self, herb_name):
        from flask import request
        herbs = []
        found = False

        # Read all herbs from the CSV
        with open('herbs_data.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row["Herb name"] == herb_name:
                    found = True
                    # Update with new data from the request
                    updated_data = request.get_json()
                    row["Herb name"] = updated_data.get("name", row["Herb name"])
                    row["Scientific Name"] = updated_data.get("scientific_name", row["Scientific Name"])
                    row["Medicinal properties"] = updated_data.get("medicinal_properties", row["Medicinal properties"])
                    row["Usage "] = updated_data.get("usage", row["Usage "])
                    row["Side effects"] = updated_data.get("side_effects", row["Side effects"])
                    row["Region/Origin"] = updated_data.get("region_origin", row["Region/Origin"])
                herbs.append(row)

        if not found:
            return {"message": f"Herb {herb_name} not found."}, 404

        # Write back the updated data to the CSV
        with open('herbs_data.csv', mode='w', newline='') as file:
            fieldnames = ["Herb name", "Scientific Name", "Medicinal properties", "Usage ", "Side effects", "Region/Origin"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(herbs)

        return {"message": f"Herb {herb_name} updated successfully."}, 200
  
  
  
  
  
  
    def delete(self, herb_name):
        herbs = []
        found = False

        # Read all herbs and filter out the one to delete
        with open('herbs_data.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row["Herb name"] == herb_name:
                    found = True
                    continue
                herbs.append(row)

        if not found:
            return {"message": f"Herb {herb_name} not found."}, 404

        # Write back the remaining herbs to the CSV
        with open('herbs_data.csv', mode='w', newline='') as file:
            fieldnames = ["Herb name", "Scientific Name", "Medicinal properties", "Usage ", "Side effects", "Region/Origin"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(herbs)

        return {"message": f"Herb {herb_name} deleted successfully."}, 200
