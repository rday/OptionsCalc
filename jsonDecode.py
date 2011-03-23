import re

"""
GOAL
I want to read JSON from a google feed, however the data they
send is malformed. Their JSON looks like:

{key:"value"}

No quotes around the key. So this is a quick and ugly recursive
parser I setup to parse the JSON without requiring quotes around
the keys.

- www.ryanday.net
"""

def getKey(str):
    ''' If you want to read valid JSON, use this:
        return re.findall('"(.*?)"', str)[0]
    
        To read invalid JSON (from the stream I
        am forced to use) you should use: '''
    return re.findall('(.*?):', str)[0]

def decode(str):
    '''
        This is a recursive function, but we still have to loop because
        there can be several string:value in an object, or values in
        an array. Each value should recursively call decode, but we
        have to loop through each comma separated value in our current
        value... does that make sense?
    '''
    idx = spaces = 0
    while str[idx] == ' ':
        idx = idx + 1
        spaces = spaces + 1
    if str[idx] == '{':
        ''' Loop through the current object and add
            each key/value pair '''
        obj = {}
        tmp = idx
        while str[idx] != '}':
            idx = idx + 1
            while str[idx] == ' ' or str[idx] == ',':
                idx = idx + 1
            key = getKey(str[idx:])
            ''' Find the : and decode after that '''
            while str[idx] != ':': idx = idx + 1
            idx = idx + 1
            (length, value) = decode(str[idx:])
            obj[key] = value
            idx = idx + length
        ''' skip terminating } '''
        idx = idx + 1
        ''' idx - tmp gives us the length of the entire in the json string
            object we are returning '''
        return (idx-tmp, obj)
    if str[idx] == '[':
        ''' Loop through the current array and add each item '''
        l = []
        tmp = idx
        while str[idx] != ']':
            idx = idx + 1
            while str[idx] == ' ' or str[idx] == ',':
                idx = idx + 1
            (length, value) = decode(str[idx:])
            idx = idx + length
            l.append(value)
            ''' skip terminating ] '''
        idx = idx + 1
        ''' idx - tmp gives us the length of the entire in the json string
            object we are returning '''
        return (idx-tmp,l)
    if str[idx] == '"':
        ''' If we find quotes, grab everything to the terminating quote '''
        idx = idx + 1
        s = re.findall('(.*?)"', str[idx:])[0]
        ''' length includes quotes and any space skipped at the
            beginning of the string '''
        return (len(s)+2+spaces, s)

    ''' If we haven't matched any special chars, as well as the quotes,
        we are reading an integer. So read until we hit a stopping character '''
    tmp = ''
    while str[idx] != ',' and str[idx] != ' ' and str[idx] != ']' and str[idx] != '}':
        tmp = tmp + str[idx]
        idx = idx + 1
    try:
        return (len(tmp), int(tmp))
    except:
        return (len(tmp), float(tmp))

if __name__ == "__main__":
    str1 = '{key:"first value",expires:[ {date:"1-2-3"} , {date:"4-5-6"} , {date:"7-8-9"}],key2:"value2",key3:[1,[2,4,6],  3],key4:{subkey1: "subvalue1"}}'
    list1 = '["one","and two", 3]'
    (l, obj) = decode(str1)
    arr = obj['key3']
    assert arr[1] == [2,4,6]
    assert obj['expires'][2] == {'date':'7-8-9'}
    assert obj['key'] == 'first value'
    assert obj['key4']['subkey1'] == 'subvalue1'
    assert obj['key3'][2] == 3
    (l, obj) = decode(list1)
    assert obj[1] == 'and two'
    assert obj[2] == 3
    print 'Decoder tested ok'
    f = open('google.feed')
    line = f.read()
    (l, obj) = decode(line)
    print obj
