def filter_dict(original: dict, keys: list) -> dict:
    return {k: original.get(k, "") for k in keys}


def add_data_preview_options(device: dict, data_product_ids: str, plot_number: int):
    """
    Add data preview options to the device dict.

    The format is like this for data_product_ids="3,4" and plot_number=2:
    "dataPreviewOptions": [
      {
        "data_product_format_id": 3,
        "plot_number": 1
      },
      {
        "data_product_format_id": 3,
        "plot_number": 2
      },
      {
        "data_product_format_id": 4,
        "plot_number": 1
      },
      {
        "data_product_format_id": 4,
        "plot_number": 2
      },

    ]


    """
    data_product_id_list = [
        int(dp_id.strip())
        for dp_id in data_product_ids.split(",")
        if dp_id.strip().isdigit()
    ]
    data_preview_options = []
    for dp_id in data_product_id_list:
        for plot_num in range(1, plot_number + 1):
            data_preview_options.append(
                {
                    "dataProductFormatId": dp_id,
                    "plotNumber": plot_num,
                }
            )
    return device | {"dataPreviewOptions": data_preview_options}
