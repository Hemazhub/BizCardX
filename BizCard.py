import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import pandas as pd
import mysql.connector as sql
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re

# Connecting to SQL Database
mydb = sql.connect(host='localhost',
                   user = 'root',
                   password = 'Mysql@2023',
                   database = 'BizCard')
cursor = mydb.cursor()

# Page configuration
icon = ('OCR.jpeg')
st.set_page_config(page_title= 'BizCardX',
                   page_icon=icon,
                   layout='wide',
                   initial_sidebar_state='expanded'
                   )

# Creating page
option = option_menu(menu_title=None,
                     options=['Home','Upload & Extract','Modify'],
                     icons=['house','cloud-upload','pencil-square'],
                     default_index=0,
                     orientation='horizontal',
                     styles={'backgroundColor':'#d0d0d4',
                             'secondaryBackgroundColor':'#fffdfd',
                             'primaryColor':'#225ece',
                             'textColor':'#0c0c0c'})

# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'])

# Home Menu
if option == 'Home':
    col1,col2 = st.columns(2)
    with col1:
        st.image('img_to_text.jpg', use_column_width='always')
    with col2:
        st.title('BizCardX: Extracting Business Card Data with OCR')
        st.write('A Streamlit application that allows users to upload '
                 'an image of a business card and extract relevant information from it using easyOCR.')

# upload and Extract menu
if option == 'Upload & Extract':
    st.markdown("Upload a Business Card Below")
    upl_card = st.file_uploader('Upload Here', label_visibility='collapsed',type= ['png','jpg','jpeg'])

    if upl_card is not None:

        def save_card(upl_card):
            with open(os.path.join('biz_cards',upl_card.name),'wb') as f:
                f.write(upl_card.getbuffer())
        save_card(upl_card)

        def image_preview(image,res):
            for (bbox, text, prob) in res:
                # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15, 15)
            plt.axis('off')
            plt.imshow(image)

        # Displaying the uploaded card
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### You have uploaded the card")
            st.image(upl_card)
        # DISPLAYING THE CARD WITH HIGHLIGHTS
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            with st.spinner("Please wait processing image..."):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd() + "\\" + "biz_cards" + "\\" + upl_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### Image Processed and Data Extracted")
                st.pyplot(image_preview(image, res))


        # easy OCR
        saved_img = os.getcwd() + "\\" + "biz_cards" + "\\" + upl_card.name
        result = reader.readtext(saved_img, detail=0, paragraph=False)

        #Converting image to binary to upload the sql data
        def img_to_binary(image):
            #Convert image to binary
            with open(image,'rb') as image:
                binaryData = image.read()
            return binaryData

        data = {'company_name':[],
                'card_holder_name' :[],
                'Designation' :[],
                'Mob_num' :[],
                'email' :[],
                'website':[],
                'Area' :[],
                'City' :[],
                'State' :[],
                'PINCODE' :[]}

        def get_data(res):
            for ind,i in enumerate(res):
                #to get url
                if 'www' in i.lower() or 'www.' in i.lower():
                    data['website'].append(i)
                elif 'www' in i:
                    data['website']= res[4] +'.'+ res[5]

                #To get email id
                elif '@' in i:
                    data['email'].append(i)

                #To get mobile number
                elif '-' in i:
                    data['Mob_num'].append(i)
                    if len(data['Mob_num']) ==2:
                        data['Mob_num'] = '&'.join(data['Mob_num'])

                #To get company name
                elif ind == len(res)-1:
                    data['company_name'].append(i)

                #To get name
                elif ind == 0:
                    data['card_holder_name'].append(i)

                #To get designation
                elif ind == 1:
                    data['Designation'].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+',i):
                    data["Area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["Area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["City"].append(match1[0])
                elif match2:
                    data["City"].append(match2[0])
                elif match3:
                    data["City"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                     data["State"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["State"].append(i.split()[-1])
                if len(data["State"])== 2:
                    data["State"].pop(0)

                # To get PINCODE
                if len(i)>=6 and i.isdigit():
                    data["PINCODE"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["PINCODE"].append(i[10:])
        get_data(result)

        #Creating Database
        def create_df(data):
            df = pd.DataFrame(data)
            return df
        df = create_df(data)
        st.success('Data Extracted !!!')
        st.write(df)

        if st.button('Upload data to Database'):
            # for i,row in df.iterrows():
            #     query = '''INSERT INTO bizcard_data VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            #     cursor.execute(query,tuple(row))
            #     mydb.commit()
            # st.success('Data Uploaded Sucessfully !!!')
            rows = list(df.itertuples(index=False, name=None))
            for i in rows:
                query = '''INSERT INTO bizcard_data VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                cursor.execute(query,i)
                mydb.commit()

#Modify menu
if option == 'Modify':
    col1,col2,col3 = st.columns([1.5,1.5,1], gap = 'Large')
    with col2:
        st.markdown('Alter/Delete data here')
    column1,column2 = st.columns(2,gap='large')

    try:
        with column1:
            cursor.execute('select card_holder_name from bizcard_data')
            result = cursor.fetchall()
            bizz_cards = {}
            for i in result:
                bizz_cards[i[0]] = i[0]
            selected_card = st.selectbox('Select a card holder name to update', list(bizz_cards.keys()))
            st.markdown('Update/Modify any data here')
            cursor.execute("SELECT company_name, card_holder_name, Designation, Mob_num, email, website, Area, City, State,PINCODE from bizcard_data where card_holder_name = '(selected_card)'")
            result = cursor.fetchone()

            #displaying all the info
            company_name = st.text_input("company_name", result[0])
            card_holder_name = st.text_input("card_holder_name", result[1])
            Designation = st.text_input("Designation", result[2])
            Mob_num = st.text_input("Mob_Num", result[3])
            email = st.text_input("email", result[4])
            website = st.text_input("website", result[5])
            Area = st.text_input("Area", result[6])
            City = st.text_input("City", result[7])
            State = st.text_input("State", result[8])
            PINCODE = st.text_input("PINCODE", result[9])

            if st.button('Commit changes to database'):
                # Update the information for the selected business card in the database
                cursor.execute("""UPDATE bizcard_data SET company_name=%s,card_holder_name=%s,Designation=%s,mob_num=%s,email=%s,website=%s,area=%s,city=%s,state=%s,PINCODE=%s
                                 WHERE card_holder_name=%s""", (company_name,card_holder_name,Designation,Mob_num,email,website,Area,City,State,PINCODE,selected_card))
                mydb.commit()
                st.success('Data Modified Sucessfully!!!')

        with column2:
            cursor.execute('SELECT card_holder_name from bizcard_data')
            result = cursor.fetchall()
            bizz_cards = {}
            for i in result:
                bizz_cards[i[0]] = i[0]
            selected_card = st.selectbox('Select a card holder name to Delete', list(bizz_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to Delete this card?")

            if st.button("Yes Delete the Card"):
                cursor.execute(f"DELETE FROM bizcard_data WHERE card_holder_name='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted from database.")
    except:
        st.warning('There is no data available in the database. Please Try again !!!')


    if st.button('View Updated Card Data'):
        cursor.execute('SELECT company_name, card_holder_name, Designation, Mob_num, email, website, Area, City, State,PINCODE FROM bizcard_data')
        Modified_df = pd.DataFrame(cursor.fetchall(), columns=['company_name', 'card_holder_name', 'Designation', 'Mob_num', 'email', 'website', 'Area', 'City', 'State','PINCODE'])
        st.write(Modified_df)