# -*- coding: utf-8 -*-
"""SemanticDataProcessingApp.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zQZiZw5_INUdm32TDZyM-zu74MUbXN_1
"""

!pip install -I flask-ngrok
!pip install -I pandas==0.25
!pip install -I pandas-profiling
!pip install -I Flask-WTF

from flask import Flask,request,send_file
from flask_ngrok import run_with_ngrok
from wtforms import StringField, validators
from flask_wtf import Form

app = Flask(__name__)

run_with_ngrok(app)   

class APIInputValidator(Form):
  admission_csv_path = StringField('admission_csv_path', [validators.DataRequired()])
  notes_csv_path = StringField('notes_csv_path', [validators.DataRequired()])
  patient_mapping_csv_path = StringField('patient_mapping_csv_path', [validators.DataRequired()])
  processesed_data_csv_path = StringField('processesed_data_csv_path', [validators.DataRequired()])
@app.route("/")
def home():
    return "<h1>Semantic Health ML Based Data Process App</h1>"

@app.route('/processPatientData', methods = ['POST'])
def processPatientData():
  #try:
    csv_files = dict()
    form = APIInputValidator(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
      csv_files['admission_csv_path'] = request.form['admission_csv_path']
      csv_files['notes_csv_path'] = request.form['notes_csv_path']
      csv_files['patient_mapping_csv_path'] = request.form['patient_mapping_csv_path']
      csv_files['processesed_data_csv_path'] = request.form['processesed_data_csv_path']
      formated_dataframe = processColumnInPatientDataFiles(csv_files)
      formated_dataframe.to_csv('patient_consolidated_data.csv')
      return send_file('patient_consolidated_data.csv')
    else:
      return "Invalid input"
  #except Exception as e:
      #return str(e)
app.run()

#Data Processing Algorithm
import pandas as pd
import numpy as np

#CSV File Column Validation Colection
admission_validate = ['id', 'citizen_number', 'admission_date', 'admision_type', 'discharge_date', 'admission_notes']
notes_validate = ['id',	'first_name',	'last_name',	'reg_number',	'doctors_note',	'remarks']
proccessed_data_validate = ['id',	'processed_by',	'patient_number',	'admission_date',	'admission_time',	'admission_type',	'final_notes',	'final_remarks']
patient_mapping_validate= ['citizen_number',	'patient_number']

def processColumnInPatientDataFiles(files):
  #Load All Files
  admission=pd.read_csv(files["admission_csv_path"])
  notes=pd.read_csv(files["notes_csv_path"])
  patient_mapping=pd.read_csv(files["patient_mapping_csv_path"])
  proccessed_data=pd.read_csv(files["processesed_data_csv_path"])
  #Validate files for all coulmn exists
  if admission_validate != [c for c in admission.columns]:
      return 'Patient Admission has invalid columns'
  if notes_validate != [c for c in notes.columns]:
      return 'Patient Notes has invalid columns'
  if patient_mapping_validate != [c for c in patient_mapping.columns]:
      return 'Patient Mapping has invalid columns'
  if proccessed_data_validate != [c for c in proccessed_data.columns]:
      return 'Patient Processed Data has invalid columns'
  """## Initiate formatted dataframe with Patient Notes"""

  patient_dataframe=notes

  """### Get patient number and other info from registration number"""

  patient_dataframe['dept']= [dpt[0:2] for dpt in patient_dataframe["reg_number"].to_list()]
  patient_dataframe['patient_number']= [dpt[2:8] for dpt in patient_dataframe["reg_number"].to_list()]
  patient_dataframe['visit_year']= [dpt[8:] for dpt in patient_dataframe["reg_number"].to_list()]
  patient_dataframe['patient_number']=patient_dataframe['patient_number'].astype('int64')

  """### Map citizen number on patient numbner"""

  patient_dataframe=pd.merge(patient_dataframe, patient_mapping, on="patient_number")

  """### map tables based on patient id"""

  patient_dataframe=pd.merge(patient_dataframe, proccessed_data[['processed_by',	'patient_number',	'admission_date',	'admission_time',	'admission_type',	'final_notes',	'final_remarks']], on="patient_number")
  patient_dataframe = patient_dataframe.rename({'admission_date': 'proccessed_admission_date', 'admission_time': 'proccessed_admission_time','admission_type':'proccessed_admission_type'}, axis='columns')

  """### map remaining tables based on citizen_number"""

  patient_dataframe=pd.merge(patient_dataframe, admission[['citizen_number', 'admission_date', 'admision_type', 'discharge_date', 'admission_notes']], on="citizen_number")

  """### process and explore admission and processed admission date """

  patient_dataframe['proccessed_admission_date'] =  pd.to_datetime(patient_dataframe['proccessed_admission_date']).dt.date
  patient_dataframe['admission_date'] =  pd.to_datetime(patient_dataframe['admission_date']).dt.date

  """ if admission type equal procceesed admision type, del duplicate coliumn"""

  if patient_dataframe['proccessed_admission_type'].equals(patient_dataframe['admision_type']):
    del patient_dataframe['proccessed_admission_type']

  """### check where proccessed date is not equal date """

  patient_dataframe['proccessed_admission_date'].equals(patient_dataframe['admission_date'])

  patient_dataframe['proccessed_admission_date'].where(patient_dataframe['proccessed_admission_date']!=patient_dataframe['admission_date']).unique()

  """this mean all the rows in the processed date are equal to admission date except where nan, which mean unproccessed patients. hence add a boolean column that patient is proccesed or not """

  patient_dataframe['proccessed_admission_date']==patient_dataframe['admission_date']

  patient_dataframe['is_patient_proccessed']=(patient_dataframe['proccessed_admission_date']==patient_dataframe['admission_date']).to_list()
  del patient_dataframe['proccessed_admission_date']
  return patient_dataframe

