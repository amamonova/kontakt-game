import script
import pandas as pd
m = script.KontaktModel()
df = pd.read_csv('wide_wikt_means.csv')

global_success = 0

def test():
    global global_success
    sample = df.sample(1).iloc[0]
    size = min(3, len(sample.title))
    answer = m.predict_word(sample.meaning, sample.title[:size])
    print(f'Word: {sample.title}; Answer: {answer}')
    if answer == sample.title:
        global_success += 1


for i in range(0, 1000):
    test()

print(f'Total accuracy: {100 * global_success / 1000}%')

