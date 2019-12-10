import script
import pandas as pd
m = script.KontaktModel()
df = pd.read_csv('wide_wikt_means.csv')

global_success = 0
prefix = int(input())

def test():
    global global_success
    sample = df.sample(1).iloc[0]
    size = min(prefix, len(sample.title))
    answer = m.predict_word(sample.meaning, sample.title[:size])
    print(f'Word: {sample.title}; Answer: {answer}')
    if answer == sample.title:
        global_success += 1

value = 0
for test_i in range(0, 5):
    global_success = 0
    for i in range(0, 1000):
        test()
    value += 100 * global_success / 1000
    print(f'Total accuracy: {100 * global_success / 1000}%')
print(f'Mean accuracy: {value / 5}')

