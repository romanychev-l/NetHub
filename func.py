def correct_view(obj):
    res = {}
    try:
        res['id'] = obj['chat_id']
        res['title'] = obj['title']
        res['admins'] = obj['admins']
        res['members'] = obj['members']
        res['inviteLink'] = 'https://t.me/' + obj['username']
        res['description'] = obj['description']
        res['logo'] = obj['logo']

        status = obj['status']
        res['status'] = status
        if status == 'offline':
            res['date'] = obj['date'] * 1000

        res['subcategories'] = obj['subcategories']
        category_id = obj['category_id']
        res['category_id'] = category_id

    except Exception as e:
        print(e)
        res = {}

    return res

