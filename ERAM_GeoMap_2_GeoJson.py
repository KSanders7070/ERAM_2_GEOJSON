import os
import sys
import logging
from lxml import etree as ET
import geojson

# Setup Logging
def setup_logging(output_directory):
    log_file = os.path.join(output_directory, "ERAM_GeoMap_2_GeoJson.log")
    logging.basicConfig(filename=log_file, filemode='w', level=logging.INFO,  # Overwrite the log file
                        format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Script started.")

# Parse Arguments
def parse_arguments():
    if len(sys.argv) < 3:
        print("Usage: ERAM_GeoMap_2_GeoJson.py <GeoMaps.xml path> <output directory> [custom properties flag]")
        sys.exit(1)

    geomaps_xml_path = sys.argv[1]
    output_directory = sys.argv[2]
    custom_properties_flag = False  # Default

    if len(sys.argv) > 3:
        custom_properties_flag = parse_custom_flag(sys.argv[3])

    return geomaps_xml_path, output_directory, custom_properties_flag

def parse_custom_flag(arg):
    if arg.upper() in ["T", "ON"]:
        return True
    elif arg.upper() in ["F", "OFF"]:
        return False
    else:
        print("Error: Invalid value for custom properties flag. Please use 'T', 'ON', 'F', or 'OFF'.")
        sys.exit(1)

# Validate Paths
def validate_paths(geomaps_xml_path, output_directory):
    if not os.path.isfile(geomaps_xml_path):
        print(f"Error: The GeoMaps.xml file does not exist at the specified path: {geomaps_xml_path}")
        sys.exit(1)

    if not os.path.isdir(output_directory):
        print(f"Error: The output directory does not exist: {output_directory}")
        sys.exit(1)

# Convert DMS to Decimal
def convert_dms_to_decimal(dms_coordinate):
    try:
        degrees = int(dms_coordinate[:2])
        minutes = int(dms_coordinate[2:4])
        seconds = int(dms_coordinate[4:6])
        direction = dms_coordinate[-1]

        decimal = degrees + minutes / 60 + seconds / 3600
        if direction in ['S', 'W']:
            decimal *= -1

        return decimal
    except Exception as e:
        logging.error(f"Failed to convert DMS to decimal for coordinate {dms_coordinate}: {str(e)}")
        raise

# Store Defaults for Line/Symbol/Text
def store_defaults(element):
    defaults = {}
    defaults['line'] = element.find("DefaultLineProperties/GeoLineFilters")
    defaults['symbol'] = element.find("DefaultSymbolProperties/GeoSymbolFilters")
    defaults['text'] = element.find("TextDefaultProperties/GeoTextFilters")
    return defaults

# Get Filter Group with Fallback to Defaults
def get_filter_group(element, element_type, defaults):
    # Initialize filter_group_element as None
    filter_group_element = None

    if element_type == "Line":
        filter_group_element = element.find("GeoLineFilters")
        if filter_group_element is None:
            filter_group_element = defaults['line']
    elif element_type == "Symbol":
        filter_group_element = element.find("GeoSymbolFilters")
        if filter_group_element is None:
            filter_group_element = defaults['symbol']
    elif element_type == "Text":
        filter_group_element = element.find("GeoTextFilters")
        if filter_group_element is None:
            filter_group_element = defaults['text']

    # If we still have not found the FilterGroup, log the error
    if filter_group_element is None or len(filter_group_element) == 0:
        logging.error(f"Missing or empty FilterGroup for {element_type} at line {element.sourceline}")
        sys.exit(1)

    # Return a list of FilterGroup text values
    return filter_group_element.xpath("FilterGroup/text()")

# Create Output Directories
def create_output_directories(geo_map_records, output_directory):
    for record in geo_map_records:
        geomap_id = record.find("GeomapId").text
        label1 = record.find("LabelLine1").text
        label2 = record.find("LabelLine2").text
        dir_name = f"{geomap_id}-{label1}_{label2}"

        geomap_dir = os.path.join(output_directory, dir_name)

        if os.path.exists(geomap_dir):
            logging.info(f"Directory {geomap_dir} already exists. Deleting and recreating.")
            os.system(f'rmdir /S /Q "{geomap_dir}"')

        os.makedirs(geomap_dir)
        logging.info(f"Created directory: {geomap_dir}")

        for i in range(1, 21):
            os.makedirs(os.path.join(geomap_dir, f"FILTER_{str(i).zfill(2)}"))

        os.makedirs(os.path.join(geomap_dir, "Multi-Filter"))

# Parse GeoMaps.xml
def parse_geo_maps(geomaps_xml_path):
    try:
        parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(geomaps_xml_path, parser)
        root = tree.getroot()
        return root.findall(".//GeoMapRecord")
    except ET.XMLSyntaxError as e:
        logging.error(f"XML Parsing Error at line {e.lineno}, column {e.offset}: {e.msg}")
        sys.exit(1)

# Build GeoJSON Feature
def build_geojson_feature(elements, element_type, custom_properties_flag):
    coordinates = []
    properties = {}

    for element in elements:
        if element_type == "Line":
            start_lat = convert_dms_to_decimal(element.find("StartLatitude").text)
            start_lon = convert_dms_to_decimal(element.find("StartLongitude").text)
            end_lat = convert_dms_to_decimal(element.find("EndLatitude").text)
            end_lon = convert_dms_to_decimal(element.find("EndLongitude").text)

            if not coordinates or (coordinates[-1][-1] != [start_lon, start_lat]):
                coordinates.append([])

            coordinates[-1].append([start_lon, start_lat])
            coordinates[-1].append([end_lon, end_lat])

            if custom_properties_flag:
                properties["ksanders7070_MapObjectType"] = element.find("MapObjectType").text if element.find("MapObjectType") is not None else "Unknown"
                properties["ksanders7070_MapGroupId"] = element.find("MapGroupId").text if element.find("MapGroupId") is not None else "Unknown"
                properties["ksanders7070_LineObjectId"] = element.find("LineObjectId").text if element.find("LineObjectId") is not None else "Unknown"

        elif element_type == "Symbol":
            lat = convert_dms_to_decimal(element.find("Latitude").text)
            lon = convert_dms_to_decimal(element.find("Longitude").text)
            coordinates.append([lon, lat])

            if custom_properties_flag:
                properties["ksanders7070_MapObjectType"] = element.find("MapObjectType").text if element.find("MapObjectType") is not None else "Unknown"

        elif element_type == "Text":
            lat = convert_dms_to_decimal(element.find("Latitude").text)
            lon = convert_dms_to_decimal(element.find("Longitude").text)
            coordinates.append([lon, lat])

            properties["text"] = [element.find("SymbolId").text if element.find("SymbolId") is not None else "Unknown"]

            if custom_properties_flag:
                properties["ksanders7070_MapObjectType"] = element.find("MapObjectType").text if element.find("MapObjectType") is not None else "Unknown"

    feature = geojson.Feature(geometry=geojson.MultiLineString(coordinates) if element_type == "Line" else geojson.Point(coordinates), properties=properties)
    return feature

# Save GeoJSON Feature
def save_geojson_feature(geojson_feature, output_directory, filter_group, geo_map_id, label1, label2):
    # Construct the directory name based on GeomapId, LabelLine1, and LabelLine2
    dir_name = f"{geo_map_id}-{label1}_{label2}"
    full_dir_path = os.path.join(output_directory, dir_name, f"FILTER_{str(filter_group).zfill(2)}")

    # Ensure the directory exists
    os.makedirs(full_dir_path, exist_ok=True)

    # Construct the file name and path
    file_name = f"Filter_{filter_group}_{geo_map_id}.geojson"
    file_path = os.path.join(full_dir_path, file_name)

    # Save the GeoJSON file
    with open(file_path, 'w') as geojson_file:
        geojson.dump(geojson_feature, geojson_file, indent=2)

    logging.info(f"GeoJSON feature saved: {file_path}")

# Process Elements and Save GeoJSON
def process_elements_and_save(geo_map_data, output_directory, custom_properties_flag):
    for record in geo_map_data:
        geo_map_id = record.find("GeomapId").text
        label1 = record.find("LabelLine1").text
        label2 = record.find("LabelLine2").text

        defaults = store_defaults(record.find("GeoMapObjectType"))  # Store defaults for this GeoMapObjectType

        for line in record.findall(".//GeoMapLine"):
            filter_groups = get_filter_group(line, "Line", defaults)
            feature = build_geojson_feature([line], "Line", custom_properties_flag)
            for filter_group in filter_groups:
                save_geojson_feature(feature, output_directory, filter_group, geo_map_id, label1, label2)

        for symbol in record.findall(".//GeoMapSymbol"):
            filter_groups = get_filter_group(symbol, "Symbol", defaults)
            feature = build_geojson_feature([symbol], "Symbol", custom_properties_flag)
            for filter_group in filter_groups:
                save_geojson_feature(feature, output_directory, filter_group, geo_map_id, label1, label2)

            text = symbol.find(".//GeoMapText")
            if text:
                filter_groups = get_filter_group(text, "Text", defaults)
                feature = build_geojson_feature([text], "Text", custom_properties_flag)
                for filter_group in filter_groups:
                    save_geojson_feature(feature, output_directory, filter_group, geo_map_id, label1, label2)

        defaults.clear()  # Clear defaults after processing each GeoMapObjectType

# Main Execution
if __name__ == "__main__":
    try:
        geomaps_xml_path, output_directory, custom_properties_flag = parse_arguments()
        validate_paths(geomaps_xml_path, output_directory)
        setup_logging(output_directory)

        geo_map_data = parse_geo_maps(geomaps_xml_path)
        create_output_directories(geo_map_data, output_directory)
        process_elements_and_save(geo_map_data, output_directory, custom_properties_flag)

        logging.info("Script completed successfully.")
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}. Check the log file for details.")
        input("Press Enter to exit...")
