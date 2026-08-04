from template import template3b

json_filename = "Cascadia_Basin_Devices"
page_title = "Cascadia Basin Monitoring"

# 1. Run the new custom template (Title, Map, SOO Plots, Scalar Plots)
template3b(json_filename, page_title,zoom=6)