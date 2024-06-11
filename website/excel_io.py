from pandas                         import DataFrame, read_excel

from website                        import XLSX_DIR
from website                        import SUBSETS, SECTIONS

class ExcelIO :
    def __init__(self) :
        pass

    def read_dataset(self, file : str) -> None :
        df = read_excel(file)
 
        print('Drop unnecessary columns')
        replace = [(124, 220), (122, 214), (93, 217), (91, 213)]
        for src, tgt in replace :
            column = df.columns[src]
            df.drop(column, axis=1, inplace=True)
            df.rename(columns={df.columns[tgt] : column}, inplace=True)

        delete_columns = [(249, 258), (226, 248), (218, 224), (214, 216), (203, 212), (197, 200), (119, 121), (90, 92), (20, 21), (18, 19), (0, 2)]
        for start, end in delete_columns :
            df.drop(df.columns[start:end], axis=1, inplace=True)

        print('Filling empty cells')
        df.columns = df.columns.str.replace('\u0027', '\'', regex=True)
        df.replace('\u0027', '\'', regex=True, inplace=True)
        df.replace('\u2013', '\'', regex=True, inplace=True)
        df.fillna('Not Applicable', inplace=True)
        df.replace('[N|n]\/[A/a]|\b[N|n][A|a]\b|\b[N|n]o\b|None', 'Not Applicable', regex=True, inplace=True)
        df.replace(' \(.*\)', '', regex=True, inplace=True)
        df.replace(' :\(', '', regex=True, inplace=True)

        print('Validating Other responses')
        valid_answers = {
            17 : ['I don\'t have any chronic diseases', 'Asthma', 'Allergies', 'Dermatologic diseases', 'Gastroenterology diseases', 'Neurological diseases', 'Thyroid diseases', 'Cardiovascular diseases', 'Psychiatric conditions', 'Sleep disturbances/sleep-awakening diseases', 'Carbohydrate disorders', 'Other'],
            22 : ['I did not use such services', 'Stress', 'Personality disorders', 'Anxiety disorders', 'Eating disorders', 'Sleep disturbances/sleep disorders', 'Mood disorders', 'Psychotic disorders', 'Post-traumatic stress disorders', 'Self-harming', 'Addictions', 'Other'],
            24 : ['Fear of my own risk of infection, illness, and death', 'Fear of the possibility of infection, illness, and death of loved ones', 'Financial uncertainty', 'Changes awaiting the world after the pandemic', 'Isolation', 'Loneliness', 'A radical change in style and way of life because of the pandemic', 'Uncertainty about the quality of education', 'Uncertainty about finding a job after graduation', 'To find new friends', 'To find boyfriend/girlfriend', 'Limited contact with friends/loved ones', 'Nothing is difficult', 'Other'],
            25 : ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Sikhism', 'Judaism', 'Bahaism or Bahai Faith', 'Confucianism', 'Taoism', 'I am an unbeliever, I do not believe in the existence of deities or God', 'Other'],
            58 : ['Medical (doctor\'s recommendations)', 'Improving the diet', 'Maintenance of health', 'Increasing or maintaining strength, muscle mass', 'Increasing energy levels', 'Increasing muscle recovery after exercise', 'Boosting immunity', 'Increasing endurance (physical condition)', 'On the recommendation of the trainer/parent/friend', 'Because others do that', 'I like their taste', 'To increase or lose some weight', 'Improve overall sports performance', 'Due to allergies/food intolerances', 'Special diet needs', 'Of convenience - when I am hungry or thirsty', 'Other'],
            85 : ['I am not at a risk group', 'I have already had COVID-19 and now I don\'t need COVID-19 vaccination', 'The vaccine was developed too quickly, there is too little / no evidence that the vaccine is effective', 'Vaccines have significant side effects, I don\'t want to expose myself to it', 'Too many companies produce COVID-19 vaccine, I don\'t know which one I can trust', 'I have concerns about vaccine content', 'I trust neither pharmaceutical companies nor doctors', 'Vaccines themselves can induce COVID-19', 'COVID-19 is just normal flu, it does not require getting vaccinated', 'COVID-19 pandemics was invented by the government/media, thus, no vaccine is needed', 'I prefer other protection strategies against COVID-19 infection', 'I do not receive any vaccines and I won\'t do that in this case as well', 'I don\'t want to be vaccinated due to religious/cultural reasons', 'I do not have sufficient funds/insurance to afford the vaccine', 'I have good immunity and I won\'t have COVID-19', 'I have had a bad experience with vaccines in the past, so I don\'t want to get vaccinated', 'Other']
        }
        for index, allowed_list in valid_answers.items() :
            column = df.columns[index]
            for answer in df[column].unique() :
                items = answer.split(', ')
                for item in items :
                    if item not in allowed_list:
                        df[column] = df[column].replace(r'\b%s\b' % (item), 'Other', regex=True)

        print('Splitting multi-choice responses')
        multi_choices = {
            17 : ['I don\'t have any chronic diseases', 'Asthma', 'Allergies', 'Dermatologic diseases', 'Gastroenterology diseases', 'Neurological diseases', 'Thyroid diseases', 'Cardiovascular diseases', 'Psychiatric conditions', 'Sleep disturbances/sleep-awakening diseases', 'Carbohydrate disorders', 'Other'],
            18 : ['No', 'Yes, first degree relatives (parents/children)', 'Yes, distant relatives', 'Yes, friend/s', 'I don\'t know'],
            20 : ['No', 'Yes, first degree relatives (parents/children)', 'Yes, distant relatives', 'Yes, friend/s'],
            22 : ['I did not use such services', 'Stress', 'Personality disorders', 'Anxiety disorders', 'Eating disorders', 'Sleep disturbances/sleep disorders', 'Mood disorders', 'Psychotic disorders', 'Post-traumatic stress disorders', 'Self-harming', 'Addictions', 'Other'],
            58 : ['Medical (doctor\'s recommendations)', 'Improving the diet', 'Maintenance of health', 'Increasing or maintaining strength, muscle mass', 'Increasing energy levels', 'Increasing muscle recovery after exercise', 'Boosting immunity', 'Increasing endurance (physical condition)', 'On the recommendation of the trainer/parent/friend', 'Because others do that', 'I like their taste', 'To increase or lose some weight', 'Improve overall sports performance', 'Due to allergies/food intolerances', 'Special diet needs', 'Of convenience - when I am hungry or thirsty', 'Other'],
            59 : ['I don\'t use any which improve immunity', 'Internet', 'Television', 'Friends', 'Doctor', 'Press', 'Books', 'Scientific literature', 'I don\'t know'],
            85 : ['I am not at a risk group', 'I have already had COVID-19 and now I don\'t need COVID-19 vaccination', 'The vaccine was developed too quickly, there is too little / no evidence that the vaccine is effective', 'Vaccines have significant side effects, I don\'t want to expose myself to it', 'Too many companies produce COVID-19 vaccine, I don\'t know which one I can trust', 'I have concerns about vaccine content', 'I trust neither pharmaceutical companies nor doctors', 'Vaccines themselves can induce COVID-19', 'COVID-19 is just normal flu, it does not require getting vaccinated', 'COVID-19 pandemics was invented by the government/media, thus, no vaccine is needed', 'I prefer other protection strategies against COVID-19 infection', 'I do not receive any vaccines and I won\'t do that in this case as well', 'I don\'t want to be vaccinated due to religious/cultural reasons', 'I do not have sufficient funds/insurance to afford the vaccine', 'I have good immunity and I won\'t have COVID-19', 'I have had a bad experience with vaccines in the past, so I don\'t want to get vaccinated', 'Other']
        }
        for index, allowed_list in multi_choices.items() :
            column = df.columns[index]
            df = df.join(DataFrame(columns=[f'(%s) %s' % (column, item) for item in allowed_list], data=[['Yes' if item in df.at[i, column] else 'No' for item in allowed_list] for i in range(len(df.index))]))
        df.drop(df.columns[list(multi_choices.keys())], axis=1, inplace=True)

        print('Creating PREDICTORS')
        headers = list(df)
        headers = headers[0:17] + headers[192:209] + headers[17:18] + headers[209:213] + headers[18:19] + headers[213:225] + headers[19:27] + headers[27:54] + headers[225:251] + headers[54:79] + headers[251:268] + [headers[187], headers[189], headers[186]] + headers[79:106] + [headers[188], headers[190], headers[185]] + headers[106:185] + [headers[191]]
        df = df[headers]

        for section, span in SECTIONS.items() :
            names = [f'%s_%i' % (section, (index - span[0])) for index in range(span[0], span[1])]
            df.rename(columns=dict(zip(df.columns[span[0]:span[1]], names)), inplace=True)

        print('Group numeric values')
        bounds = {
              1 : [-1,  19,  21,  26,  35],
             14 : [-1, 130, 155, 170, 180],
             15 : [-1,  30,  50,  60,  80],
             16 : [-1,  30,  50,  60,  80],
            179 : [-1,   1,  5,   12,  16],
            180 : [-1,   1,  5,   12,  16],
            209 : [-1,   1,  5,   12,  16],
            210 : [-1,   1,  5,   12,  16]
        }
        for index, bound in bounds.items() :
            column = df.columns[index]
            for i in range(len(bound), 0, -1) :
                column = df.columns[index]
                df[column] = df[column].astype(int)
                df.loc[df[column] > bound[(i - 1)], column] = (-i)

        print('Modifying numeric values to nominal')
        nominals = {
            (  1,   2) : ['< 19', '19-20', '21-25', '26-35', '> 35'],
            ( 14,  15) : ['< 130', '130-154', '155-169', '170-179', '> 180'],
            ( 15,  17) : ['< 30', '30-49', '50-59', '60-80', '> 80'],
            (179, 181) : ['< 1', '1-4', '5-11', '12-16', '> 16'],
            (209, 211) : ['< 1', '1-4', '5-11', '12-16', '> 16']
        }
        for section, allowed_list in nominals.items() :
            for index in range(section[0], section[1]) :
                for answer in range(len(allowed_list)) :
                    column = df.columns[index]
                    df[column] = df[column].astype(str)
                    df.loc[df[column] == f'%i' % (-1 - answer), column] = allowed_list[answer]

        nominals = {
            (155, 156) : ['< 15 minutes', '16-30 minutes', '31-60 minutes', '> 60 minutes'],
            (156, 157) : ['> 7 hours', '6-7 hours', '5-6 hours', '< 5 hours'],
            (157, 158) : ['> 85%', '75-84%', '65-74%', '< 65%'],
            (185, 186) : ['< 15 minutes', '16-30 minutes', '31-60 minutes', '> 60 minutes'],
            (186, 187) : ['> 7 hours', '6-7 hours', '5-6 hours', '< 5 hours'],
            (187, 188) : ['> 85%', '75-84%', '65-74%', '< 65%'],
            (215, 236) : ['It doesn\'t apply to me at all now', 'This applies to me now to some extent or for a time', 'This applies to me a lot now or for a long time', 'It applies to me very much now or most of the time']
        }
        for section, allowed_list in nominals.items() :
            for index in range(section[0], section[1]) :
                for answer in range(len(allowed_list)) :
                    column = df.columns[index]
                    df[column] = df[column].astype(str)
                    df.loc[df[column] == f'%i' % (answer), column] = allowed_list[answer]

        nominals = {
            (  3,   4) : ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6'],
            ( 55,  56) : ['Never', 'Once a year or less', 'A few times a year', 'A few times a month', 'Once a week', 'More than once/week'],
            ( 56,  57) : ['Rarely or never', 'A few times a month', 'Once a week', 'Two or more times/week', 'Daily', 'More than once a day'],
            ( 57,  60) : ['Definitely not true', 'Tends not to be true', 'Unsure', 'Tends to be true', 'Once a week', 'Definitely true of me'],
            (236, 264) : ['I hardly ever do that', 'I rarely do this', 'I do this often', 'I almost always do this']
        }
        for section, allowed_list in nominals.items() :
            for index in range(section[0], section[1]) :
                for answer in range(len(allowed_list)) :
                    column = df.columns[index]
                    df[column] = df[column].astype(str)
                    df.loc[df[column] == f'%i' % (answer + 1), column] = allowed_list[answer]

        print('Creating LABELS')
        df.loc[df['PSQI'] < 5, 'PSQI'] = 1
        df = df.astype(str)
        for i in range(len(SUBSETS)) :
            df.rename(columns={df.columns[i + len(headers) - len(SUBSETS)] : SUBSETS[i]}, inplace=True)
            df.loc[df[SUBSETS[i]] == '1',      SUBSETS[i]] = 'Normal'
            df.loc[df[SUBSETS[i]] != 'Normal', SUBSETS[i]] = 'Possible'
        df[df.columns[-4:]].to_excel(f'%s/ALL_LABELS.xlsx' % (XLSX_DIR), index=False)

        drop_groups = {
            'DEPRESSION' : [f'DASS-21_%i' % i for i in [0, 5, 7, 10, 11, 13, 17]],
            'ANXIETY'    : [f'DASS-21_%i' % i for i in [1, 3, 6, 8, 14, 18, 19]],
            'STRESS'     : [f'DASS-21_%i' % i for i in [2, 4, 9, 12, 15, 16, 20]],
            'SLEEP'      : [f'PSQI_%i' % i for i in range(60)]
        }
        for subset in SUBSETS :
            print(f'Creating excel and arff files for %s subset' % (subset))
            df_subset = df[df.columns[:-4]].drop(drop_groups[subset], axis=1).join(df[subset])
            df_subset.to_excel(f'%s/%s_ALL.xlsx' % (XLSX_DIR, subset), index=False)

    def save_excel(self, file : str, df : DataFrame) -> None :
        df.to_excel(f'%s/%s.xlsx' % (XLSX_DIR, file), index=False)

    def load_excel(self, file : str) -> DataFrame :
        return read_excel(f'%s/%s.xlsx' % (XLSX_DIR, file)).astype(str)