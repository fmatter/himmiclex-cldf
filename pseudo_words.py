import random
vcl_plos = "p t k".split(" ")
vcd_plos = "b d g".split(" ")
vcl_obs = "t͡ʃ s".split(" ")
vcd_obs = "d͡ʒ z".split(" ")
nasals = "m n ɲ ŋ".split(" ")
appr = "r l j w".split(" ")
glottals = "h ʔ".split(" ")
vowels = "a e i o u ə ɨ".split(" ")

def get_rand(list):
    return list[random.randint(0,len(list)-1)]

def coin():
    toss = random.randint(1,2)
    if toss == 1:
        return True
    else:
        return False

onsetl = vcl_plos + vcd_plos + vcl_obs + vcd_obs + nasals + appr
def onset(output):
    output += get_rand(onsetl)
    if output in vcl_plos + vcd_plos and coin():
        output += get_rand(appr)
    return output
    
def v(output):
    return output + get_rand(vowels)

codal = nasals + glottals + vcl_plos
def coda(output):
    if coin():
        output += get_rand(codal)
    return output

def pseudo_word():
    output = ""
    i = 0
    while True:
        output = onset(output)
        output = v(output)
        i += 1
        if i > 0:
            if random.randint(1,2) < i:
                output = coda(output)
                break
    return output