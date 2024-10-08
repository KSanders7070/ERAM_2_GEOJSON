# SCRIPT OVERVIEW

## INPUT/OUTPUT

The script that will take data from a RW ERAM GeoMaps.xml and create geojson files in accordance with RFC-7946 format standards for use by the program CRC.
The script will create .geojsons that are Linestrings (including multilinestrings), Symbols, and Text.
Each geojson will contain only one of these types and appened `_Lines` `_Symbols` and `_Text` at the end of the .geojson name accordingly.

Via arguments, the user will provide the path to the geomaps.xml file and then in the second argument the directory for the output location.

A third argument will be a T/F boolean turning Custom Properties on or off (off by default). More details explained later in this document.

## OUTPUT DIRECTORY SETUP

First the script will find each `<GeoMapRecord>`.

Inside of that GeoMapRecord, get the `<GeomapId>` value and the `<LabelLine1>` and `<LabelLine2>` values. Create folders in the output directory that follow this format: `<GeomapId>`-`<LabelLine1>`_`<LabelLine2>`
Example: **CENTER-CTR_MAP**  
*Note: If the `<GeomapId>` folder already exists, the script will delete that directory and subdirectories and content, and remake it.*

In each folder that was made, create subdirectories "Filter_01", "Filter_02", etc... up to and including "Filter_20".
Also create a folder labeled "Multi-Filter".  
*Note: When creating directories, Filter numbers must always be made with 2 digits but prefixing zeros should not be added to file name or other data later.*

## LINES, SYMBOLS, TEXT

In `<GeomapId>`-`GeoMapObjectType`

- `GeoMapLine` = Linestring object `_Lines.geojson`
- `GeoMapSymbol` = Symbol object `_Symbols.geojson`
  - However, there may also be a `GeoMapText` within `GeoMapSymbol` and that data will be a Text object `_Text.geojson`

## FILTERGROUP ASSIGNMENT

To know what filter directory to place the .geojson in, the script will need to know the FilterGroup that is assigned to that data.

- For Lines (GeoMapLine)
  - First look for the FilterGroup in `GeoMapObjectType`-`GeoMapLine`-`GeoLineFilters` but if it is not there, get it from `GeoMapObjectType`-`DefaultLineProperties`-`GeoLineFilters`.
    - It is important to look in this order because the data in `GeoMapObjectType`-`GeoMapLine`-`GeoLineFilters` overrides `GeoMapObjectType`-`DefaultLineProperties`-`GeoLineFilters`.
- For Symbols (GeoMapSymbol without GeoMapText)
  - First look for the FilterGroup in `GeoMapObjectType`-`GeoMapSymbol`-`GeoSymbolFilters` but if it is not there, get it from `GeoMapObjectType`-`DefaultSymbolProperties`-`GeoSymbolFilters`.
    - It is important to look in this order because the data in `GeoMapObjectType`-`GeoMapSymbol`-`GeoSymbolFilters` overrides `GeoMapObjectType`-`DefaultSymbolProperties`-`GeoSymbolFilters`.
- For Text (GeoMapSymbol with GeoMapText)
  - First look for the FilterGroup in `GeoMapObjectType`-`GeoMapSymbol`-`GeoMapText`-`GeoTextFilters` but if it is not there, get it from `GeoMapObjectType`-`TextDefaultProperties`-`GeoTextFilters`.
    - It is important to look in this order because the data in `GeoMapObjectType`-`GeoMapSymbol`-`GeoMapText`-`GeoTextFilters` overrides `GeoMapObjectType`-`TextDefaultProperties`-`GeoTextFilters`.

## COORDINATES

Coordinates retrieved from the .xml will be in DMS format such as "37000000N" and need to be converted to decimal format for the .geojson.

Coordinates may be found for the objects as follows:

For Lines:

- `GeoMapObjectType`-`GeoMapLine`-`StartLatitude`
- `GeoMapObjectType`-`GeoMapLine`-`StartLongitude`

For Symbols & Text:

- `GeoMapObjectType`-`GeoMapSymbol`-`Latitude`
- `GeoMapObjectType`-`GeoMapSymbol`-`Longitude`

## OUTPUT DIRECTORY AND FILE NAME

The completed geojson file will be saved in the Filter_## folder designated by the FilterGroup.

If more than one FilterGroup is assigned, the file will be saved in the Multi-Filter folder with a subdirectory created with the following format organizing the assigned FilterGroups in numerical order:
`Filters_##_##_##` etc...  
Example: if there was one or more elements with a filtergroup assignment of 8,2,1,12 the following directory would be created: `...Multi-Filter\Filters_01_02_08_12`

Multiple like-elements with identical filter assignments will be output to the same .geojson.  
For example, if one line-type element has a FilterGroup of "3,5,13" and later on in the .xml another line-type element has that also has a FilterGroup assignment of "3,5,13", these two elements will be placed togheter in the same ..._Lines.geojson

Name of the outout file will follow the following format:  
`<same as the host directory>`_`<Lines/Symbols/Text>`.geojson

Examples:

- ...\Filters_01\
  - Filter_01_Lines.geojson
  - Filter_01_Symbols.geojson
  - Filter_01_Text.geojson
- ...\Filters_13\
  - Filter_13_Lines.geojson
  - Filter_13_Symbols.geojson
  - Filter_13_Text.geojson
- ...\Multi-Filter\Filters_02_04_05_11\
  - Filter_02_04_05_11_Lines.geojson
  - Filter_02_04_05_11_Symbols.geojson
  - Filter_02_04_05_11_Text.geojson

## CUSTOM PROPERTIES

Custom Properties will be information from the .xml that is not needed to make the geojson but may be helpful with testing and organization by the Facility Engineer (person that manages the .geojson files). This feature is turned off (F) by default.

Not all tags and elements will carry over into the geojson; Below you will find information for exactly how this information is handled and when it is passed in to the .geojson.

In order to avoid future confliction with other .geojson readers, the properties keys will be the tag name from the .xml but prefixed with "ksanders7070_".

FOR LINES:

- If the user elects to have Custom Properties turned on, the script will insert a custom key/values into the properties section of the feature detailing the .xml's MapObjectType, MapGroupId, and LineObjectId.
  - Example:
    - "ksanders7070_MapObjectType": "ApproachControl"
    - "ksanders7070_MapGroupId": "1"
    - "ksanders7070_LineObjectId": "DTW"

FOR SYMBOLS:

- If the user elects to have Custom Properties turned on, the script will insert a custom key/values into the properties section of the feature detailing the .xml's MapObjectType.
  - Example:
    - "ksanders7070_MapObjectType": "WAYPOINT"

FOR TEXT:

- If the user elects to have Custom Properties turned on, the script will insert a custom key/values into the properties section of the feature detailing the .xml's MapObjectType.

- Regardless if the user elects to have custom properties turned on or not, the script will create a property key of "text" and assign it the value for the .xml's tag SymbolId. Format: `"text": ["<SymbolId>"]`
  - Example:
    - "ksanders7070_MapObjectType": "WAYPOINT"
    - "text": ["ALEEE"]

- Along with creating the text feature in the _Text.geojson,the script will also create a feature for this text element as a "Symbol" in the `_Symbols`.geojson file using the same FilterGroup value. (i.e., after creating the text feature, run the symbol feature aswell but add the same `"text": ["<SymbolId>"]` property in the symbols file.)

## EFFICIENT LINESTRING HANDLING

To save space and organization of the .geojson line files, we will combine MapObjectType, MapGroupId, and LineObjectId together.

For example, if MapObjectType=ApproachControl, MapGroupId=1, and the LineObjectId=BUF, then all LineObjectId elements that match that sequence of attributes will be grouped together in the same Feature.

If the current StartLatitude and StartLongitude is equal to the previous EndLatitude and EndLongitude, then just add the current EndLatitude and EndLongitude to the same linestring. When the current StartLatitude and StartLongitude are not equal to the previous EndLatitude and EndLongitude, create a break in the multilinestring.

Example

```json
{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"MultiLineString","coordinates":[[[-108.79043292472375,40.8506145555433],[-102.2181888812155,37.06641395317544],[-108.9552885445442,40.80903657260835]],[[-108.3837890625,40.46711432758179],[-105.2,37.1]]]},"properties":{"ksanders7070_MapObjectType":"ApproachControl","ksanders7070_MapGroupId":"1","ksanders7070_LineObjectId":"BUF"}},{"type":"Feature","geometry":{"type":"MultiLineString","coordinates":[[[-109.1,41.8],[-103.1,38.1],[-109.2,41.9]],[[-107.2,41.3],[-108.2,42.3]]]},"properties":{"ksanders7070_MapObjectType":"ApproachControl","ksanders7070_MapGroupId":"2","ksanders7070_LineObjectId":"BUF"}},{"type":"Feature","geometry":{"type":"MultiLineString","coordinates":[[[-111.1,42.8],[-108.1,39.1],[-110.2,42.9]],[[-105.2,40.70000000000001],[-105.3,40.8]]]},"properties":{"ksanders7070_MapObjectType":"ApproachControl","ksanders7070_MapGroupId":"1","ksanders7070_LineObjectId":"DTW"}}]}
```
