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


def requestToString(data):
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


with open('test_data_with_contact_phone.json', 'rb') as json_data:
    data_set = json.loads(json_data.read())
    print(len(data_set), "datas loaded succesfully")
    requestDict_for_contact_phone = {}  # store the id of posts have identical contact phone

    for data in data_set:
        content = get_from_api(data['content'])
        data['content'] = requestToString(content)  # store content after get_from_api and requestToString into hash
        if (data['contact_phone']) is not None:
            key = hashMap(str(data['contact_phone']))
            if not requestDict_for_contact_phone.get(key):
                requestDict_for_contact_phone[key] = []
            data['contact_phone'] = ''  # It's unnecessary to store contact_phone in hash, just check it's null/not
            requestDict_for_contact_phone[key].append(data)
        else:
            key = hashMap('-1')
            if not requestDict_for_contact_phone.get(key):
                requestDict_for_contact_phone[key] = []
            requestDict_for_contact_phone[key].append(data)

    #print(requestDict_for_contact_phone)

    for requestData in requestDict_for_contact_phone:
        for data in requestDict_for_contact_phone[requestData]:
            #print(data)
            output = Output()
            output.result['id'] = data['id']
            if data['contact_phone'] is None:
                output.result['agency'] = 'Not sure'    # because of no contact_phone
                # ghi file
                with codecs.open('result2.json', 'a') as reader:
                    json.dump(output.result, reader)
            else:
                if len(requestDict_for_contact_phone[requestData]) == 1:    # only 1 post => No agency
                    output.result['agency'] = 'No'
                    # ghi file
                    with codecs.open('result2.json', 'a') as reader:
                        json.dump(output.result, reader)
                elif len(requestDict_for_contact_phone[requestData]) > 20:   # more than 20 posts from the same number
                    output.result['agency'] = 'Yes'
                    print(data['id'])
                    # ghi file
                    with codecs.open('result2.json', 'a') as reader:
                        json.dump(output.result, reader)
                else:
                    conclusion = ''
                    for another_data in requestDict_for_contact_phone[requestData]:
                        if another_data['id'] == data['id']:
                            continue
                        if another_data['content'] != data['content']:
                            conclusion = 'Not sure'
                            # this contact_phone has some posts (not too much) but the content of each is
                            # different => Not sure because this case is not in rule
                            break
                    if conclusion == '':
                        conclusion = 'No'   # post more than 1 with the same content => No agency
                    # print for another post having the same number
                    for another_data in requestDict_for_contact_phone[requestData]:
                        output.result['id'] = another_data['id']
                        output.result['agency'] = conclusion
                        # ghi file
                        with codecs.open('result2.json', 'a') as reader:
                            json.dump(output.result, reader)
                    break
