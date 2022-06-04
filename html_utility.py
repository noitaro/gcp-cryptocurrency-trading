def get_history(history_data: str):

    html = '''
<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: "Open Sans", sans-serif;
            line-height: 1.25;
        }

        table {
            border-collapse: collapse;
            margin: 0 auto;
            padding: 0;
            width: auto;
            table-layout: fixed;
        }

        table tr {
            background-color: #fff;
            border: 1px solid #bbb;
            padding: .35em;
        }

        table th,
        table td {
            padding: 1em 10px 1em 1em;
            border-right: 1px solid #bbb;
        }

        table th {
            font-size: .85em;
        }

        table thead tr {
            background-color: #eee;
        }

        @media screen and (max-width: 800px) {
            table {
                border: 0;
                width: 100%
            }

            table th {
                background-color: #eee;
                display: block;
                border-right: none;
            }

            table thead {
                border: none;
                clip: rect(0 0 0 0);
                height: 1px;
                margin: -1px;
                overflow: hidden;
                padding: 0;
                position: absolute;
                width: 1px;
            }

            table tr {
                display: block;
                margin-bottom: .625em;
            }

            table td {
                border-bottom: 1px solid #bbb;
                display: block;
                font-size: .8em;
                text-align: right;
                position: relative;
                padding: .625em .625em .625em 4em;
                border-right: none;
            }

            table td::before {
                content: attr(data-label);
                font-weight: bold;
                position: absolute;
                left: 10px;
            }

            table td:last-child {
                border-bottom: 0;
            }
        }
    </style>
    <title>取引履歴</title>
</head>

<body>
    <table>
        <thead>
            <tr>
                <th scope="col">注文ID</th>
                <th scope="col">取引銘柄</th>
                <th scope="col">売買区分</th>
                <th scope="col">注文タイプ</th>
                <th scope="col">価格</th>
                <th scope="col">数量</th>
                <th scope="col">約定日時</th>
            </tr>
        </thead>
        <tbody>
    '''
    histories = history_data.splitlines()
    is_first = True
    for history in histories:
        if is_first:
            # 先頭はヘッダー行のため、飛ばす
            is_first = False
            continue
        print(history.split(','))
        data = history.split(',')
        html = html + f'''
            <tr>
                <td data-label="注文ID">{data[0]}</td>
                <td data-label="取引銘柄">{data[1]}</td>
                <td data-label="売買区分">{data[2]}</td>
                <td data-label="注文タイプ">{data[3]}</td>
                <td data-label="価格">{data[4]}</td>
                <td data-label="数量">{data[5]}</td>
                <td data-label="約定日時">{data[6]}</td>
            </tr>
        '''
        pass

    html = html + '''
        </tbody>
    </table>
</body>

</html>
    '''
    return html
