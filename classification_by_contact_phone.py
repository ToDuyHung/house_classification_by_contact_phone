import json
import codecs
import requests
import hashlib

url = "http://127.0.0.1:3005/api/v1/real-estate-extraction"


def get_from_api(post_content):
    request = requests.Session()
    data_list = [post_content]
    # print("*** \ndata_list:{}\n ***".format(data_list))
    headers = {}

    response = request.post(
        url=url,
        headers=headers,
        json=data_list
    )

    data_attrs = {
        "attr_addr_street": "",
        "attr_addr_district": "",
        "attr_addr_ward": "",
        "attr_addr_city": "",
        "attr_surrounding_name": "",
        "attr_surrounding_characteristics": "",
    }

    try:
        json_response = response.json()
        # print("\n\n\n === json_response:{} === \n\n\n".format(json_response))
        for content, i in zip(
                json_response[0]["tags"],
                range(len(
                    json_response[0]["tags"]
                ))
        ):
            if content["type"] == "addr_street" and content["content"] not in data_attrs["attr_addr_street"]:
                data_attrs["attr_addr_street"] += content["content"] + ", "

            elif content['type'] == "addr_ward" and content["content"] not in data_attrs["attr_addr_ward"]:
                data_attrs["attr_addr_ward"] += content["content"] + ", "

            elif content['type'] == "addr_district" and content["content"] not in data_attrs["attr_addr_district"]:
                data_attrs["attr_addr_district"] += content["content"] + ", "

            elif content['type'] == "addr_city" and content["content"] not in data_attrs["attr_addr_city"]:
                data_attrs["attr_addr_city"] += content["content"] + ", "

            elif content['type'] == "surrounding" and content["content"] not in data_attrs["attr_surrounding_name"]:
                data_attrs["attr_surrounding_name"] += content["content"] + ", "

            elif content["type"] == "surrounding_characteristics" and content["content"] not in data_attrs[
                "attr_surrounding_characteristics"]:
                data_attrs['attr_surrounding_characteristics'] += content["content"] + ", "

    except:
        pass
    return data_attrs


s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'


def remove_accents(input_str):
    s = ''
    for c in input_str:
        if c in s1:
            s += s0[s1.index(c)]
        else:
            s += c
    return s


def requestToString(data):  # use to convert the data gotten from get_from_api() to string
    stringRequest = ""
    for feature in data:
        new_feature = remove_accents(data[feature]).lower()
        bagOfWord = set(new_feature.split(', '))
        bagOfWord.discard('')

        new_bagOfWord = sorted(bagOfWord)
        # print(new_bagOfWord)

        for word in new_bagOfWord:
            stringRequest += word + " "
    # print(stringRequest)

    return stringRequest


def hashMap(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


class Output:
    result = {
        'id': '',
        'agency': ''  # có qua môi giới hay không ? Yes/No/Not sure
    }


with open('data_1.json', 'rb') as json_data:
    data_set = json.loads(json_data.read())
    print(len(data_set), "datas loaded succesfully")

    requestDict_for_contact_phone = {}  # store the id of posts have identical contact phone
    for data in data_set:
        if (data['contact_phone']) is not None:
            key = hashMap(str(data['contact_phone']))
            if not requestDict_for_contact_phone.get(key):
                requestDict_for_contact_phone[key] = []
            requestDict_for_contact_phone[key].append(data['id'])
        else:
            key = hashMap('-1')
            if not requestDict_for_contact_phone.get(key):
                requestDict_for_contact_phone[key] = []
            requestDict_for_contact_phone[key].append(data['id'])

    # print(requestDict_for_contact_phone)

    for requestData in requestDict_for_contact_phone:
        for data_id in requestDict_for_contact_phone[requestData]:
            # print(data_id)
            output = Output()
            output.result['id'] = data_id
            if data['contact_phone'] is None:
                output.result['agency'] = 'Not sure because no contact phone'  # because of no contact_phone
                # ghi file
                with codecs.open('result2.json', 'a') as reader:
                    json.dump(output.result, reader)
            else:
                if len(requestDict_for_contact_phone[requestData]) == 1:  # only 1 post => No agency
                    output.result['agency'] = 'No because only 1 post'
                    # ghi file
                    with codecs.open('result2.json', 'a') as reader:
                        json.dump(output.result, reader)
                elif len(requestDict_for_contact_phone[requestData]) > 20:  # more than 20 posts having the same phone
                    output.result['agency'] = 'Yes because >20 post'
                    # ghi file
                    with codecs.open('result2.json', 'a') as reader:
                        json.dump(output.result, reader)
                else:
                    conclusion = ''
                    requestDict_for_content = {}
                    data_content = ''
                    for data in data_set:
                        if data['id'] == data_id:
                            data_content = requestToString(get_from_api(data['content']))
                            break
                    content_key = hashMap(data_content)
                    requestDict_for_content[content_key] = data_id
                    for another_data_id in requestDict_for_contact_phone[requestData]:
                        if another_data_id == data_id:
                            continue
                        for data in data_set:
                            if data['id'] == another_data_id:
                                data_content = requestToString(get_from_api(data['content']))
                                break
                        content_key = hashMap(data_content)
                        if not requestDict_for_content.get(content_key):
                            conclusion = 'Not sure because < 20post and diff content'
                            # this contact_phone has < 20 posts (not too much) but the content of each is
                            # different => Not sure because this case is not in rule
                            break
                    if conclusion == '':
                        conclusion = 'No because >1 post same content'
                        # more than 1 post with the same content => No agency

                    # ghi file for all posts in this case
                    for another_data_id in requestDict_for_contact_phone[requestData]:
                        output.result['id'] = another_data_id
                        output.result['agency'] = conclusion
                        with codecs.open('result2.json', 'a') as reader:
                            json.dump(output.result, reader)
                    break
    print('Done')