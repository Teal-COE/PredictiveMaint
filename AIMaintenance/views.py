
from django.shortcuts import render , redirect



def home(requests):
    return redirect( 'predictive/login_screen')