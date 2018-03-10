# translation table
hwk = '｢｣ｧｨｩｪｫｬｭｮｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝｰｯ､ﾟﾞ･?｡'
hira = '「」ぁぃぅぇぉゃゅょあいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんーっ、？！…　。'
hwk_hira_trans = str.maketrans(hwk, hira)

def translate(line):
    return line.translate(hwk_hira_trans)

#same as above, but also un-escape any &, < or > characters
def translate_and_unescape(line):
    return translate(line.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>'))