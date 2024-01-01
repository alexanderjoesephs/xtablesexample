from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, HttpResponse
#from .forms import CustomisedUserCreationForm
from .forms import CustomUserCreationForm
from .models import Question, Attempt, User, Teacher, Student, Test, Admin, Settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
matplotlib.use('Agg')  # Set the backend to 'Agg'
from datetime import datetime
from PIL import Image







# Create your views here.
def home(request):
    """
    for i in range(2,13):
        for j in range(2,13):
            q = Question()
            q.x = i
            q.y = j
            q.save()
    """
    return render(request, "home.html")




def user_login(request):
    if(request.user.is_authenticated):
        return redirect(home)
    if request.method=='GET':
        return render(request, 'login.html')
    if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(home)
        else:
            return render(request, 'login.html',{'loginfailedmessage':"Couldn't log in user"})

def logoutview(request):
    if request.method=="POST":
        
        if request.user.is_authenticated:
            logout(request)
        return redirect(home)
    else:
        return redirect(home)



def student_ready(request):
    if not request.user_status=='student':
        return render(request,'error.html',{'error':'User not logged in as student'})
    else:
        times_tables = Test.objects.filter(user_tested=request.user,set=True)
        test_list = []
        for number in times_tables:
            test_list.append(number.table_tested)
    settings = Settings.objects.get(user=request.user)
    seconds = settings.number_of_seconds
    questions = settings.number_of_questions
    return render(request, 'student_ready.html',{'test_list':test_list,'seconds':seconds,'questions':questions})


def student_play(request):
    if not request.user_status=='student':
        return render(request,'error.html',{'error':'User not logged in as student'})
    else:
        #get all times tables this user should be tested on
        times_tables = Test.objects.filter(user_tested=request.user,set=True)
        test_list = []
        for number in times_tables:
            test_list.append(number.table_tested)
        question_list = []
        
        for test in test_list:
            for i in range(2,13):
                array = []
                array.append(test)
                array.append(i)
                question_list.append(array)
        settings = Settings.objects.get(user=request.user)
        seconds = settings.number_of_seconds
        questions = settings.number_of_questions
        print(seconds)
        print(questions)
        return render(request, 'student_play.html',{'question_list':question_list,'seconds':seconds,'questions':questions})

@csrf_exempt  # Only for example. Use CSRF protection in production.
def create_attempt(request):
    if request.method == 'POST':
        a = Attempt()
        correct = request.POST.get('correct', '')
        time_taken = request.POST.get('time_taken','')
        user = request.POST.get('user','')
        x = request.POST.get('x','')
        y = request.POST.get('y','')
        if correct == 'true':
            a.correct = True
            a.time_taken = time_taken
        if correct == 'false':
            a.correct = False
        a.user_asked = User.objects.get(username=user)
        a.question_asked = Question.objects.get(x=x,y=y)
        a.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def teacher_stats(request):
    if request.method=='GET':
        if request.user_status=='teacher':
            teacher = Teacher.objects.get(user=request.user.id)
            students = Student.objects.filter(classes=teacher)
            return render(request, 'teacher_stats.html',{'students':students})
        else:
            return render(request, 'error.html', {'error':'Account holder not teacher'})
    if request.method=='POST':
        teacher = Teacher.objects.get(user=request.user.id)
        students = Student.objects.filter(classes=teacher)
        users_ids = []
        for student in students:
            users_ids.append(student.user.id)
        print('users_of_students')
        print(users_ids)
        print(User.objects.filter(id__in=users_ids))


        data_type = request.POST.get('data type')
        student = request.POST.get('student')
        date_to = request.POST.get('date_to')
        date_from = request.POST.get('date_from')
        date_to_object = datetime.strptime(date_to, '%Y-%m-%d').date()
        date_from_object = datetime.strptime(date_from, '%Y-%m-%d').date()
        #formatting dates for f-strings
        uk_date_to_str = date_to_object.strftime('%d-%m-%Y')
        uk_date_from_str = date_from_object.strftime('%d-%m-%Y')
        uk_date_to_str = uk_date_to_str.replace('-', '/')
        uk_date_from_str = uk_date_from_str.replace('-', '/')
        if data_type=='whole class':
            attempts = Attempt.objects.filter(date_created__date__range=[date_from_object, date_to_object]).filter(user_asked__in=users_ids)
            info_string = f"Stats for whole class from {uk_date_from_str} to {uk_date_to_str}"
        if data_type=='individual student':
            info_string = f"Stats for {student} from {uk_date_from_str} to {uk_date_to_str}"
            user_asked = User.objects.get(username = student)
            attempts = Attempt.objects.filter(user_asked=user_asked).filter(date_created__date__range=[date_from_object, date_to_object])
            #put in code that creates heatmaps and graph here
        if not attempts:
            return render(request, 'error.html',{'error':'Student has not used app enough yet'})
        df = pd.DataFrame.from_records(attempts.values())
        print('df')
        print(df)
        x_list = [obj.x for obj in attempts]
        df['x'] = x_list
        y_list = [obj.y for obj in attempts]
        df['y'] = y_list
        df_cleaned = df.dropna(subset=['correct'])
        percentage_correct = df_cleaned.groupby(['x', 'y'])['correct'].mean()
        percentage_correct = percentage_correct.reset_index()

        # Create a pivot table
        pivot_table = pd.pivot_table(percentage_correct, values='correct', index='y', columns='x')

        # Display the pivot table
        #plt.figure(figsize=(10, 8))
        plt.figure(figsize=(7, 7))
        norm = plt.Normalize(vmin=0, vmax=1)
        sns.heatmap(pivot_table, annot=True, fmt=".0%", cmap="RdYlGn",norm=norm, cbar=False)
        
        
        plt.title('Percentage correct heatmap')
        plt.xlabel('')
        plt.ylabel('')
        #invert y axis
        ax = plt.gca()
        ax.invert_yaxis()
        # Save the heatmap to a temporary file or buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        with Image.open(img_buffer) as img:
            img = img.convert('RGB')  # Convert image to RGB mode if needed

            # Get image dimensions
            width, height = img.size

            # Initialize crop boundaries
            left, top, right, bottom = width, height, 0, 0

            # Scan image to find boundaries
            for x in range(width):
                for y in range(height):
                    if img.getpixel((x, y)) != (255, 255, 255):  # Check for non-white pixels (white is (255, 255, 255))
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)

            # Crop the image using identified boundaries
            cropped_img = img.crop((left - 10, top - 10, right + 10, bottom + 35))

            # Save the cropped image back to the buffer
            cropped_img_buffer = BytesIO()
            cropped_img.save(cropped_img_buffer, format='png')
            cropped_img_buffer.seek(0)
            img_str = base64.b64encode(cropped_img_buffer.read()).decode('utf-8')

        # Close the buffers
        img_buffer.close()
        cropped_img_buffer.close()

        

        df_time = df.dropna(subset=['time_taken'])
        average_time = df_time.groupby(['x', 'y'])['time_taken'].mean()/1000
        average_time = average_time.reset_index()

        pivot_table_average_time = pd.pivot_table(average_time, values='time_taken', index='y', columns='x')
        #plt.figure(figsize=(10, 8))
        plt.figure(figsize=(7, 7))
        norm = plt.Normalize(vmin=0, vmax=6.2)
        sns.heatmap(pivot_table_average_time, annot=True, fmt=".1f", cmap="RdYlGn_r",norm=norm, cbar=False)
        plt.title('Average time of correct answers heatmap')
        plt.xlabel('')
        plt.ylabel('')
        #invert y axis
        ax = plt.gca()
        ax.invert_yaxis()
        img_buffer2 = BytesIO()
        plt.savefig(img_buffer2, format='png')
        img_buffer2.seek(0)


        with Image.open(img_buffer2) as img:
            img = img.convert('RGB')  # Convert image to RGB mode if needed

            # Get image dimensions
            width, height = img.size

            # Initialize crop boundaries
            left, top, right, bottom = width, height, 0, 0

            # Scan image to find boundaries
            for x in range(width):
                for y in range(height):
                    if img.getpixel((x, y)) != (255, 255, 255):  # Check for non-white pixels (white is (255, 255, 255))
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)

            # Crop the image using identified boundaries
            cropped_img = img.crop((left - 10, top - 10, right + 10, bottom + 35))

            # Save the cropped image back to the buffer
            cropped_img_buffer = BytesIO()
            cropped_img.save(cropped_img_buffer, format='png')
            cropped_img_buffer.seek(0)
            img_str2 = base64.b64encode(cropped_img_buffer.read()).decode('utf-8')

        # Close the buffers
        img_buffer2.close()
        cropped_img_buffer.close()

        #get the effort charts here
        if data_type=='individual student':
            user_asked = User.objects.get(username = student)
            attempts = Attempt.objects.filter(user_asked=user_asked).filter(date_created__date__range=[date_from_object, date_to_object])
            effort_df = pd.DataFrame.from_records(attempts.values())
            total_attempts = len(effort_df)
            print(effort_df)
            effort_df['date_created'] = pd.to_datetime(df['date_created'])

            # Extract the day from the 'date_created' column
            effort_df['day'] = effort_df['date_created'].dt.date

            # Group by 'day' and count the number of rows for each day
            
            grouped_by_day = effort_df.groupby('day').size().reset_index(name='count')
            
            print(grouped_by_day)
            plt.figure(figsize=(6, 6))
            sns.barplot(x='day', y='count', data=grouped_by_day,color=(255/255, 255/255, 120/255))
            plt.title(f'{total_attempts} questions grouped by day.')
            plt.xlabel('Day')
            plt.ylabel('Attempts')
            
            
            img_buffer3 = BytesIO()
            plt.savefig(img_buffer3, format='png')
            img_buffer3.seek(0)
            img_str3 = base64.b64encode(img_buffer3.read()).decode('utf-8')

            grouped_by_correct = effort_df.groupby('correct').size().reset_index(name='count').replace({True: 'Correct', False: 'Incorrect'})
            print(grouped_by_correct)
            plt.figure(figsize=(6, 6))
            colours = [(255/255, 185/255, 147/255), (177/255, 222/255, 113/255)]
            sns.barplot(x='correct', y='count', hue='correct', data=grouped_by_correct, palette=colours, legend=False)
            plt.title(f'{total_attempts} questions grouped by correctness.')
            plt.xlabel('Correct')
            plt.ylabel('Attempts')
            img_buffer4 = BytesIO()
            plt.savefig(img_buffer4, format='png')
            img_buffer4.seek(0)
            img_str4 = base64.b64encode(img_buffer4.read()).decode('utf-8')
            context = {'students':students,'heatmap_image': img_str,'heatmap_image2': img_str2,'student':student,'info_string':info_string,'heatmap_image3':img_str3,'heatmap_image4':img_str4}
        if data_type=='whole class':
            attempts = Attempt.objects.filter(date_created__date__range=[date_from_object, date_to_object]).filter(user_asked__in=users_ids)
            effort_df = pd.DataFrame.from_records(attempts.values())
            print(effort_df)
            grouped_by_user = effort_df.groupby('user_asked_id').size().reset_index(name='count')
            grouped_by_user['name'] = grouped_by_user['user_asked_id'].apply(lambda x: User.objects.get(id=x).username)
            grouped_by_user = grouped_by_user.sort_values(by='count', ascending=False)
            plt.figure(figsize=(14, 6))
            # Create bar plot
            ax = sns.barplot(x='count', y='name', data=grouped_by_user, color=(255/255, 255/255, 120/255))
            ax.set_yticklabels([f"{name} ({count} attempts)" for name, count in zip(grouped_by_user['name'], grouped_by_user['count'])])
            # Modify x-axis labels to include count
            
            plt.title('Questions attempted for each student')
            plt.xlabel('Attempts')
            plt.ylabel('Students')
            img_buffer5 = BytesIO()
            plt.savefig(img_buffer5, format='png')
            img_buffer5.seek(0)
            img_str5 = base64.b64encode(img_buffer5.read()).decode('utf-8')
            context = {'students':students,'heatmap_image': img_str,'heatmap_image2': img_str2,'student':student,'info_string':info_string,'heatmap_image5': img_str5}
        # Pass the base64-encoded image string to the template
        return render(request, 'teacher_stats.html',context)
        


def teacher_set_work(request):
    if request.method == "GET":
        if request.user_status=='teacher':
            this_teacher = Teacher.objects.get(user = request.user)
            students = Student.objects.filter(classes=this_teacher)
            array_of_tables = []
            array_of_settings = []
            for student in students:
                user = User.objects.get(id=student.user.id)
                tables = Test.objects.filter(user_tested=user)
                array_of_tables.append(tables)
                settings = Settings.objects.filter(user=user)
                array_of_tables.append(settings)
            
            print('studnets')
            print(students)
            print('array_of_tables')
            print(array_of_tables)
            print('array_of_tables length')
            print(len(array_of_tables))
            return render(request,'teacher_set_work.html',{'students':students,'array_of_tables':array_of_tables})
        else:
            return render(request,'error.html',{'error':'Not logged in as teacher.'})
    if request.method == "POST":
        print(request.POST)
        results = request.POST.getlist('set')
        this_teacher = Teacher.objects.get(user = request.user)
        students = Student.objects.filter(classes=this_teacher)
        for student in students:
            user_student = User.objects.get(username=student)
            tests_set_to_student = Test.objects.filter(user_tested=user_student)
            for test in tests_set_to_student:
                string = test.user_tested.username + ':' + str(test.table_tested)
                if string in results:
                    test.set = True
                else:
                    test.set = False
                test.save()
        
        
        for student in students:
            print('printing student')
            print(student)
            questions =  request.POST.get(f'{student}questions')
            seconds =  request.POST.get(f'{student}seconds')
            user_settings = User.objects.get(username=student)
            settings = Settings.objects.get(user=user_settings)
            settings.number_of_questions = questions
            settings.number_of_seconds = seconds
            settings.save()

            

        array_of_tables = []
        for student in students:
                user = User.objects.get(id=student.user.id)
                tables = Test.objects.filter(user_tested=user)
                array_of_tables.append(tables)
                settings = Settings.objects.filter(user=user)
                array_of_tables.append(settings)
        
        return render(request,'teacher_set_work.html',{'students':students,'array_of_tables':array_of_tables,'update_message':'Work set has been updated.'})
    

def teacher_print_flashcards(request):
    if request.method == "GET":
        if request.user_status=='teacher':
            return render(request,'teacher_print_flashcards.html')
        else:
            return render(request,'error.html',{'error':'Not logged in as teacher.'})
    if request.method == "POST":
        date_to = request.POST.get('date_to')
        date_from = request.POST.get('date_from')
        date_to_object = datetime.strptime(date_to, '%Y-%m-%d').date()
        date_from_object = datetime.strptime(date_from, '%Y-%m-%d').date()
        teacher = Teacher.objects.get(user=request.user.id)
        students = Student.objects.filter(classes=teacher).values('user')
        users = User.objects.filter(id__in=students).values('username')
        student_dict = {item['username']: None for item in users}
        for key in student_dict:
            id = User.objects.get(username=key)
            tests = Test.objects.filter(user_tested=id).filter(set=True)
            list_of_tables = []
            for test in tests:
                list_of_tables.append(test.table_tested)
            questions = Question.objects.filter(x__in=list_of_tables)
            query = Attempt.objects.filter(user_asked=id).filter(question_asked__in=questions).filter(date_created__date__range=[date_from_object, date_to_object])
            df = pd.DataFrame.from_records(query.values())
            if not df.empty:
                
                grouped = df.groupby('question_asked_id').agg(
                total_questions=pd.NamedAgg(column='id', aggfunc='count'),
                total_correct=pd.NamedAgg(column='correct', aggfunc='sum'),
                mean_time_taken=pd.NamedAgg(column='time_taken', aggfunc='mean')
                ).reset_index()

                # Calculate percentage correct
                grouped['percentage_correct'] = (grouped['total_correct'] / grouped['total_questions']) * 100
                
                #only keep results under 95 correct
                under95 = grouped[grouped['percentage_correct']<95].sort_values(by='percentage_correct')
                #print(under95)

                if len(under95)<10:
                    rows_needed = 10 - len(under95)
                    over95 =  grouped[grouped['percentage_correct']>=95]
                    over95_sorted_by_time = over95.sort_values(by='mean_time_taken',ascending=False)
                    over_95_rows_needed = over95_sorted_by_time.head(rows_needed)
                    #print(over_95_rows_needed)
                    ten_worst = pd.concat([under95, over_95_rows_needed], axis=0, ignore_index=True)
                else:
                    ten_worst = under95.head(10)
                #print(ten_worst)
                ten_worst_list = ten_worst['question_asked_id'].to_list()
                question_list = []
                for i in ten_worst_list:
                    q = Question.objects.get(id=i)
                    question_string = f"{q.x} x {q.y}"
                    question_list.append(question_string)
                student_dict[key] = question_list
            else:
                student_dict[key] = []
        print(student_dict)
        return render(request,'teacher_print_flashcards.html',{'student_dict':student_dict,'date_to':date_to,'date_from':date_from})



def teacher_download_pdf(request,date_from,date_to):
    if not request.user_status=='teacher':
        return render(request,'error.html',{'error':'User not teacher'})
    else:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="class_set_tables.pdf"'
        teacher = Teacher.objects.get(user=request.user.id)
        students = Student.objects.filter(classes=teacher)
        date_to_object = datetime.strptime(date_to, '%Y-%m-%d').date()
        date_from_object = datetime.strptime(date_from, '%Y-%m-%d').date()
        #Get dimensions of the letter page
        width, height = letter

        # Define the number of columns and rows
        num_columns = 2
        num_rows = 5

        # Set a larger font size for the text (size 45)
        font_size = 55

        # Create a canvas object for the first page
        c = canvas.Canvas(response, pagesize=letter)

        for student in students:
            list_of_tables = []
            tests = Test.objects.filter(user_tested=student.user).filter(set=True)
            print('tests')
            print(tests)
            for test in tests:
                list_of_tables.append(test.table_tested)
            print(list_of_tables)

            #get list of set questions
            questions = Question.objects.filter(x__in=list_of_tables)
            print(questions)

            
            query = Attempt.objects.filter(user_asked=student.user).filter(question_asked__in=questions).filter(date_created__date__range=[date_from_object, date_to_object])
            df = pd.DataFrame.from_records(query.values())
            if not df.empty:
                grouped = df.groupby('question_asked_id').agg(
                total_questions=pd.NamedAgg(column='id', aggfunc='count'),
                total_correct=pd.NamedAgg(column='correct', aggfunc='sum'),
                mean_time_taken=pd.NamedAgg(column='time_taken', aggfunc='mean')
                ).reset_index()
            
                # Calculate percentage correct
                grouped['percentage_correct'] = (grouped['total_correct'] / grouped['total_questions']) * 100
            
                #only keep results under 95 correct
                under95 = grouped[grouped['percentage_correct']<95].sort_values(by='percentage_correct')
                #print(under95)

                if len(under95)<10:
                    rows_needed = 10 - len(under95)
                    over95 =  grouped[grouped['percentage_correct']>=95]
                    over95_sorted_by_time = over95.sort_values(by='mean_time_taken',ascending=False)
                    over_95_rows_needed = over95_sorted_by_time.head(rows_needed)
                    #print(over_95_rows_needed)
                    ten_worst = pd.concat([under95, over_95_rows_needed], axis=0, ignore_index=True)
                else:
                    ten_worst = under95.head(10)
                #print(ten_worst)
                ten_worst_list = ten_worst['question_asked_id'].to_list()
                question_list = []
                answer_list = []
                for i in ten_worst_list:
                    q = Question.objects.get(id=i)
                    question_string = f"{q.x} x {q.y}"
                    answer_string = f"{q.answer}"
                    question_list.append(question_string)
                    answer_list.append(answer_string)
            else:
                ten_worst_list = []
                question_list = []
                answer_list = []

            if len(ten_worst_list)<10:
                missing = 10 - len(ten_worst_list)
                for i in range(missing):
                    question_list.append('')
                    answer_list.append('')

            for i in [0,2,4,6,8]:
                mem = question_list[i]
                question_list[i] = question_list[i+1]
                question_list[i+1] = mem

            print(answer_list)

        


            
            c.setFont("Helvetica", font_size)

            # Draw dotted grids and add text for the first page
            for row in range(num_rows + 1):  # +1 to draw the bottommost horizontal line
                y = row * (height / num_rows)
                c.setStrokeColor(colors.black)
                c.setDash(3, 3)  # Set a 3x3 dot pattern for dotted lines
                c.line(0, y, width, y)

            for col in range(num_columns + 1):  # +1 to draw the rightmost vertical line
                x = col * (width / num_columns)
                c.line(x, 0, x, height)

            
            question_index = 0
            # Add text to each grid cell for the first page
            for row in range(num_rows-1,-1,-1):
                for col in range(num_columns-1,-1,-1):
                    x_start = col * (width / num_columns)
                    x_end = (col + 1) * (width / num_columns)
                    y_start = row * (height / num_rows)
                    y_end = (row + 1) * (height / num_rows)

                    # Calculate the center of the cell to place text
                    x_center = (x_start + x_end) / 2
                    y_center = (y_start + y_end) / 2
                    
                    # Generate a unique identifier for each cell
                    cell_text = question_list[question_index]
                    question_index = question_index + 1

                    # Place text in the center of each cell
                    c.drawString(x_center - (c.stringWidth(cell_text, "Helvetica", font_size) / 2), y_center - (font_size / 2), cell_text)
            small_font_size = 15
            c.setFont("Helvetica", small_font_size)

            #trying to put name of flash card owner
            for row in range(num_rows-1,-1,-1):
                for col in range(num_columns-1,-1,-1):
                    x_start = col * (width / num_columns)
                    x_end = (col + 1) * (width / num_columns)
                    y_start = row * (height / num_rows)
                    y_end = (row + 1) * (height / num_rows)

                    # Calculate the center of the cell to place text
                    x_center = (x_start + x_end) / 2
                    y_center = ((y_start + y_end) / 2) + 50
                    
                    # Generate a unique identifier for each cell
                    cell_text = student.user.username

                    # Place text in the center of each cell
                    c.drawString(x_center - (c.stringWidth(cell_text, "Helvetica", small_font_size) / 2), y_center - (small_font_size / 2), cell_text)

            # Show the first page and start a new page for the second page
            c.showPage()

            # Repeat for the second page
            c.setFont("Helvetica", font_size)

            # Draw dotted grids for the second page
            for row in range(num_rows + 1):  # +1 to draw the bottommost horizontal line
                y = row * (height / num_rows)
                c.setStrokeColor(colors.black)
                c.setDash(3, 3)  # Set a 3x3 dot pattern for dotted lines
                c.line(0, y, width, y)

            for col in range(num_columns + 1):  # +1 to draw the rightmost vertical line
                x = col * (width / num_columns)
                c.line(x, 0, x, height)
            answer_index = 0
            # Add text to each grid cell for the second page
            for row in range(num_rows-1,-1,-1):
                for col in range(num_columns-1,-1,-1):
                    x_start = col * (width / num_columns)
                    x_end = (col + 1) * (width / num_columns)
                    y_start = row * (height / num_rows)
                    y_end = (row + 1) * (height / num_rows)

                    # Calculate the center of the cell to place text
                    x_center = (x_start + x_end) / 2
                    y_center = (y_start + y_end) / 2

                    # Generate a unique identifier for each cell
                    cell_text = answer_list[answer_index]
                    answer_index = answer_index + 1
                    # Place text in the center of each cell
                    c.drawString(x_center - (c.stringWidth(cell_text, "Helvetica", font_size) / 2), y_center - (font_size / 2), cell_text)
            
            # Show the first page and start a new page for the second page
            c.showPage()

    # Save the PDF
    c.save()
        
        
    return response
    


def class_flash(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="class_set_tables.pdf"'

    if not Teacher.objects.filter(user=request.user.id):
        print('not teach')
        return redirect(home)
    teacher = Teacher.objects.get(user=request.user.id)
    students = Student.objects.filter(classes=teacher)

    # Get dimensions of the letter page
    width, height = letter

    # Define the number of columns and rows
    num_columns = 2
    num_rows = 5

    # Set a larger font size for the text (size 45)
    font_size = 55

    # Create a canvas object for the first page
    c = canvas.Canvas(response, pagesize=letter)

    for student in students:
        list_of_tables = []
        tests = Test.objects.filter(user_tested=student.user).filter(set=True)
        print('tests')
        print(tests)
        for test in tests:
            list_of_tables.append(test.table_tested)
        print(list_of_tables)

        #get list of set questions
        questions = Question.objects.filter(x__in=list_of_tables)
        print(questions)

        
        query = Attempt.objects.filter(user_asked=student.user).filter(question_asked__in=questions)
        df = pd.DataFrame.from_records(query.values())
        df = pd.DataFrame.from_records(query.values())
        grouped = df.groupby('question_asked_id').agg(
        total_questions=pd.NamedAgg(column='id', aggfunc='count'),
        total_correct=pd.NamedAgg(column='correct', aggfunc='sum'),
        mean_time_taken=pd.NamedAgg(column='time_taken', aggfunc='mean')
        ).reset_index()

        # Calculate percentage correct
        grouped['percentage_correct'] = (grouped['total_correct'] / grouped['total_questions']) * 100
        
        #only keep results under 95 correct
        under95 = grouped[grouped['percentage_correct']<95].sort_values(by='percentage_correct')
        #print(under95)

        if len(under95)<10:
            rows_needed = 10 - len(under95)
            over95 =  grouped[grouped['percentage_correct']>=95]
            over95_sorted_by_time = over95.sort_values(by='mean_time_taken',ascending=False)
            over_95_rows_needed = over95_sorted_by_time.head(rows_needed)
            #print(over_95_rows_needed)
            ten_worst = pd.concat([under95, over_95_rows_needed], axis=0, ignore_index=True)
        else:
            ten_worst = under95.head(10)
        #print(ten_worst)
        ten_worst_list = ten_worst['question_asked_id'].to_list()
        question_list = []
        answer_list = []
        for i in ten_worst_list:
            q = Question.objects.get(id=i)
            question_string = f"{q.x} x {q.y}"
            answer_string = f"{q.answer}"
            question_list.append(question_string)
            answer_list.append(answer_string)


        if len(question_list) > 9:
            print('list')
            print(question_list)

            for i in [0,2,4,6,8]:
                mem = answer_list[i]
                answer_list[i] = answer_list[i+1]
                answer_list[i+1] = mem

            print(answer_list)

        


            
            c.setFont("Helvetica", font_size)

            # Draw dotted grids and add text for the first page
            for row in range(num_rows + 1):  # +1 to draw the bottommost horizontal line
                y = row * (height / num_rows)
                c.setStrokeColor(colors.black)
                c.setDash(3, 3)  # Set a 3x3 dot pattern for dotted lines
                c.line(0, y, width, y)

            for col in range(num_columns + 1):  # +1 to draw the rightmost vertical line
                x = col * (width / num_columns)
                c.line(x, 0, x, height)

            
            question_index = 0
            # Add text to each grid cell for the first page
            for row in range(num_rows):
                for col in range(num_columns):
                    x_start = col * (width / num_columns)
                    x_end = (col + 1) * (width / num_columns)
                    y_start = row * (height / num_rows)
                    y_end = (row + 1) * (height / num_rows)

                    # Calculate the center of the cell to place text
                    x_center = (x_start + x_end) / 2
                    y_center = (y_start + y_end) / 2
                    
                    # Generate a unique identifier for each cell
                    cell_text = question_list[question_index]
                    question_index = question_index + 1

                    # Place text in the center of each cell
                    c.drawString(x_center - (c.stringWidth(cell_text, "Helvetica", font_size) / 2), y_center - (font_size / 2), cell_text)
            small_font_size = 15
            c.setFont("Helvetica", small_font_size)

            #trying to put name of flash card owner
            for row in range(num_rows):
                for col in range(num_columns):
                    x_start = col * (width / num_columns)
                    x_end = (col + 1) * (width / num_columns)
                    y_start = row * (height / num_rows)
                    y_end = (row + 1) * (height / num_rows)

                    # Calculate the center of the cell to place text
                    x_center = (x_start + x_end) / 2
                    y_center = ((y_start + y_end) / 2) + 50
                    
                    # Generate a unique identifier for each cell
                    cell_text = student.user.username

                    # Place text in the center of each cell
                    c.drawString(x_center - (c.stringWidth(cell_text, "Helvetica", small_font_size) / 2), y_center - (small_font_size / 2), cell_text)

            # Show the first page and start a new page for the second page
            c.showPage()

            # Repeat for the second page
            c.setFont("Helvetica", font_size)

            # Draw dotted grids for the second page
            for row in range(num_rows + 1):  # +1 to draw the bottommost horizontal line
                y = row * (height / num_rows)
                c.setStrokeColor(colors.black)
                c.setDash(3, 3)  # Set a 3x3 dot pattern for dotted lines
                c.line(0, y, width, y)

            for col in range(num_columns + 1):  # +1 to draw the rightmost vertical line
                x = col * (width / num_columns)
                c.line(x, 0, x, height)
            answer_index = 0
            # Add text to each grid cell for the second page
            for row in range(num_rows):
                for col in range(num_columns):
                    x_start = col * (width / num_columns)
                    x_end = (col + 1) * (width / num_columns)
                    y_start = row * (height / num_rows)
                    y_end = (row + 1) * (height / num_rows)

                    # Calculate the center of the cell to place text
                    x_center = (x_start + x_end) / 2
                    y_center = (y_start + y_end) / 2

                    # Generate a unique identifier for each cell
                    cell_text = answer_list[answer_index]
                    answer_index = answer_index + 1
                    # Place text in the center of each cell
                    c.drawString(x_center - (c.stringWidth(cell_text, "Helvetica", font_size) / 2), y_center - (font_size / 2), cell_text)
            
            # Show the first page and start a new page for the second page
            c.showPage()

    # Save the PDF
    c.save()

    return response


def student(request):
    if request.method=='GET':
        if Student.objects.filter(user=request.user.id):
            return render(request, 'student.html')
        else:
            return render(request, 'error.html', {'error':'Account holder not teacher'})


def student_stats(request):
    if not request.user_status=='student':
        return render(request,'error.html',{'error':'Not logged on as student'})
    else:
        if request.method == 'GET':
            return render(request,'student_stats.html')
        if request.method == "POST":
            date_to = request.POST.get('date_to')
            date_from = request.POST.get('date_from')
            date_to_object = datetime.strptime(date_to, '%Y-%m-%d').date()
            date_from_object = datetime.strptime(date_from, '%Y-%m-%d').date()
            #formatting dates for f-strings
            uk_date_to_str = date_to_object.strftime('%d-%m-%Y')
            uk_date_from_str = date_from_object.strftime('%d-%m-%Y')
            uk_date_to_str = uk_date_to_str.replace('-', '/')
            uk_date_from_str = uk_date_from_str.replace('-', '/')
            info_string = f"Your stats from {uk_date_from_str} to {uk_date_to_str}"
            attempts = Attempt.objects.filter(user_asked=request.user).filter(date_created__date__range=[date_from_object, date_to_object])
            if not attempts:
                return render(request, 'error.html',{'error':'Student has not used app enough yet'})
            df = pd.DataFrame.from_records(attempts.values())
            print('df')
            print(df)
            x_list = [obj.x for obj in attempts]
            df['x'] = x_list
            y_list = [obj.y for obj in attempts]
            df['y'] = y_list
            df_cleaned = df.dropna(subset=['correct'])
            percentage_correct = df_cleaned.groupby(['x', 'y'])['correct'].mean() 
            percentage_correct = percentage_correct.reset_index()

            # Create a pivot table
            pivot_table = pd.pivot_table(percentage_correct, values='correct', index='y', columns='x')

            # Display the pivot table
            #plt.figure(figsize=(10, 8))
            plt.figure(figsize=(7, 7))
            norm = plt.Normalize(vmin=0, vmax=1)
            sns.heatmap(pivot_table, annot=True, fmt=".0%", cmap="RdYlGn", norm=norm, cbar=False)
            plt.title('Percentage correct heatmap')
            plt.xlabel('')
            plt.ylabel('')
            #invert y axis
            ax = plt.gca()
            ax.invert_yaxis()
            # Save the heatmap to a temporary file or buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            with Image.open(img_buffer) as img:
                img = img.convert('RGB')  # Convert image to RGB mode if needed

                # Get image dimensions
                width, height = img.size

                # Initialize crop boundaries
                left, top, right, bottom = width, height, 0, 0

                # Scan image to find boundaries
                for x in range(width):
                    for y in range(height):
                        if img.getpixel((x, y)) != (255, 255, 255):  # Check for non-white pixels (white is (255, 255, 255))
                            left = min(left, x)
                            top = min(top, y)
                            right = max(right, x)
                            bottom = max(bottom, y)

                # Crop the image using identified boundaries
                cropped_img = img.crop((left - 10, top - 10, right + 10, bottom + 35))

                # Save the cropped image back to the buffer
                cropped_img_buffer = BytesIO()
                cropped_img.save(cropped_img_buffer, format='png')
                cropped_img_buffer.seek(0)
                img_str = base64.b64encode(cropped_img_buffer.read()).decode('utf-8')

            # Close the buffers
            img_buffer.close()
            cropped_img_buffer.close()

            

            df_time = df.dropna(subset=['time_taken'])
            average_time = df_time.groupby(['x', 'y'])['time_taken'].mean()/1000
            average_time = average_time.reset_index()

            pivot_table_average_time = pd.pivot_table(average_time, values='time_taken', index='y', columns='x')
            #plt.figure(figsize=(10, 8))
            plt.figure(figsize=(7, 7))
            norm = plt.Normalize(vmin=0, vmax=6.2)
            sns.heatmap(pivot_table_average_time, annot=True, fmt=".1f", cmap="RdYlGn_r",norm=norm, cbar=False)
            plt.title('Average time of correct answers heatmap')
            plt.xlabel('')
            plt.ylabel('')
            #invert y axis
            ax = plt.gca()
            ax.invert_yaxis()
            img_buffer2 = BytesIO()
            plt.savefig(img_buffer2, format='png')
            img_buffer2.seek(0)


            with Image.open(img_buffer2) as img:
                img = img.convert('RGB')  # Convert image to RGB mode if needed

                # Get image dimensions
                width, height = img.size

                # Initialize crop boundaries
                left, top, right, bottom = width, height, 0, 0

                # Scan image to find boundaries
                for x in range(width):
                    for y in range(height):
                        if img.getpixel((x, y)) != (255, 255, 255):  # Check for non-white pixels (white is (255, 255, 255))
                            left = min(left, x)
                            top = min(top, y)
                            right = max(right, x)
                            bottom = max(bottom, y)

                # Crop the image using identified boundaries
                cropped_img = img.crop((left - 10, top - 10, right + 10, bottom + 35))

                # Save the cropped image back to the buffer
                cropped_img_buffer = BytesIO()
                cropped_img.save(cropped_img_buffer, format='png')
                cropped_img_buffer.seek(0)
                img_str2 = base64.b64encode(cropped_img_buffer.read()).decode('utf-8')

            # Close the buffers
            img_buffer2.close()
            cropped_img_buffer.close()

            #Get the effort charts
           
            attempts = Attempt.objects.filter(user_asked=request.user).filter(date_created__date__range=[date_from_object, date_to_object])
            effort_df = pd.DataFrame.from_records(attempts.values())
            total_attempts = len(effort_df)
            print(effort_df)
            effort_df['date_created'] = pd.to_datetime(df['date_created'])

            # Extract the day from the 'date_created' column
            effort_df['day'] = effort_df['date_created'].dt.date

            # Group by 'day' and count the number of rows for each day
            
            grouped_by_day = effort_df.groupby('day').size().reset_index(name='count')
            
            print(grouped_by_day)
            plt.figure(figsize=(6, 6))
            sns.barplot(x='day', y='count', data=grouped_by_day,color=(255/255, 255/255, 120/255))
            plt.title(f'{total_attempts} questions grouped by day.')
            plt.xlabel('Day')
            plt.ylabel('Attempts')
            
            
            img_buffer3 = BytesIO()
            plt.savefig(img_buffer3, format='png')
            img_buffer3.seek(0)
            img_str3 = base64.b64encode(img_buffer3.read()).decode('utf-8')

            grouped_by_correct = effort_df.groupby('correct').size().reset_index(name='count').replace({True: 'Correct', False: 'Incorrect'})
            print(grouped_by_correct)
            plt.figure(figsize=(6, 6))
            colours = [(255/255, 185/255, 147/255), (177/255, 222/255, 113/255)]
            sns.barplot(x='correct', y='count', hue='correct', data=grouped_by_correct, palette=colours, legend=False)
            plt.title(f'{total_attempts} questions grouped by correctness.')
            plt.xlabel('Correct')
            plt.ylabel('Attempts')
            img_buffer4 = BytesIO()
            plt.savefig(img_buffer4, format='png')
            img_buffer4.seek(0)
            img_str4 = base64.b64encode(img_buffer4.read()).decode('utf-8')
            return render(request,'student_stats.html',{'info_string':info_string,'heatmap_image': img_str,'heatmap_image2': img_str2,'heatmap_image3': img_str3,'heatmap_image4': img_str4})



def admin_create_user(request):
    if request.method=='GET':
        if Admin.objects.filter(user=request.user.id):
            form = CustomUserCreationForm()
            return render(request,'admin_create_user.html',{'form':form})
        else:
            return render(request, 'error.html', {'error':'Account holder not admin'})
    if request.method=='POST':    
        if not request.user_status == 'admin': 
            return render(request, 'error.html', {'error':'Account holder not admin'})
        else:
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data['username']
                user_to_assign_times_tables = User.objects.get(username=username)
                admin_creating_account = Admin.objects.get(user=request.user)
                for i in range(2,13):
                    test = Test()
                    test.set = True
                    test.table_tested = i
                    test.user_tested = user_to_assign_times_tables
                    test.save()
                settings = Settings()
                settings.user = user_to_assign_times_tables
                settings.save()
                if form.cleaned_data['account_type'] == 'teacher':
                    t = Teacher()
                    t.user = user_to_assign_times_tables
                    t.admin = admin_creating_account
                    t.save()
                if form.cleaned_data['account_type'] == 'student':
                    s = Student()
                    s.user = user_to_assign_times_tables
                    s.admin = admin_creating_account
                    s.save()
                return render(request, "admin_create_user.html",{'form':form,'message':f"Successfully created user {user_to_assign_times_tables.username}"})

            else:
                
                return render(request, "admin_create_user.html",{'form':form,'message':"Couldn't create user"})
            
def admin_assign_students(request):
    if request.method=='GET':
        if not request.user_status=='admin':
            return render(request, 'error.html', {'error':'Account holder not admin'})
        if request.user_status=='admin':
            admin = Admin.objects.get(user=request.user)
            teachers = Teacher.objects.filter(admin=admin)
            students = Student.objects.filter(admin=admin).filter(classes__isnull=True)
            
            return render(request, 'admin_assign_students.html',{'students':students,'teachers':teachers})
    if request.method=='POST':
        if not request.user_status=='admin':
            return render(request, 'error.html', {'error':'Account holder not admin'})
        else:
            
            teacher_form = request.POST.get('teacher_selected')
            student_form = request.POST.getlist('student')
            user_teacher = User.objects.get(username=teacher_form)
            teacher_to_assign = Teacher.objects.get(user=user_teacher) 
            for student_name in student_form:
                
                user_student = User.objects.get(username=student_name)
                student_instance = Student.objects.get(user=user_student)
                
                student_instance.classes = teacher_to_assign
                student_instance.save()
            #get list of students and teachers again
            admin = Admin.objects.get(user=request.user)
            teachers = Teacher.objects.filter(admin=admin)
            students = Student.objects.filter(admin=admin).filter(classes__isnull=True)
        return render(request, 'admin_assign_students.html',{'students':students,'teachers':teachers,'teacher_form':teacher_form,'student_form':student_form})

def admin_remove_students(request):
    
    if request.method == "GET":
        
        if not request.user_status=='admin':
            
            return render(request, 'error.html', {'error':'Account holder not admin'})
        else:
            
            admin = Admin.objects.get(user=request.user.id)
            teachers = Teacher.objects.filter(admin=admin)
            students = Student.objects.filter(admin=admin,classes__isnull=False)
            print('teachers and students')
            print(teachers)
            print(students)
            return render(request,'admin_remove_students.html',{'teachers':teachers,'students':students})
        
    if request.method == "POST":
        if not request.user_status=='admin':
            
            return render(request, 'error.html', {'error':'Account holder not admin'})
        remove=request.POST.getlist('student_selected')
        print(remove)
        users_to_remove = User.objects.filter(username__in=remove)
        students_to_remove = Student.objects.filter(user__in=users_to_remove)
        for student_to_remove in students_to_remove:
            student_to_remove.classes=None
            student_to_remove.save()
        #make students.classes of those in the form null here
        admin = Admin.objects.get(user=request.user.id)
        teachers = Teacher.objects.filter(admin=admin)
        students = Student.objects.filter(admin=admin,classes__isnull=False)
        
        return render(request,'admin_remove_students.html',{'teachers':teachers,'students':students})


def admin_stats(request):
    if request.method=='GET':
        if request.user_status=='admin':
            admin = Admin.objects.get(user=request.user.id)
            teachers = Teacher.objects.filter(admin=admin)
            students = Student.objects.filter(admin=admin)
            print('admin, teachers, students')
            print(admin)
            print(teachers)
            print(students)
            return render(request, 'admin_stats.html',{'students':students,'teachers':teachers})
        else:
            return render(request, 'error.html', {'error':'Account holder not admin'})
    if request.method=='POST':
        
        

        teacher = request.POST.get('teacher')
        data_type = request.POST.get('data type')
        student = request.POST.get('student')
        date_to = request.POST.get('date_to')
        date_from = request.POST.get('date_from')
        date_to_object = datetime.strptime(date_to, '%Y-%m-%d').date()
        date_from_object = datetime.strptime(date_from, '%Y-%m-%d').date()
        #formatting dates for f-strings
        uk_date_to_str = date_to_object.strftime('%d-%m-%Y')
        uk_date_from_str = date_from_object.strftime('%d-%m-%Y')
        uk_date_to_str = uk_date_to_str.replace('-', '/')
        uk_date_from_str = uk_date_from_str.replace('-', '/')
        if data_type=='whole class':
            user_teacher = User.objects.get(username=teacher)
            teacher_object = Teacher.objects.get(user=user_teacher)
            students = Student.objects.filter(classes=teacher_object)
            users_ids = []
            for student in students:
                users_ids.append(student.user.id)
            attempts = Attempt.objects.filter(date_created__date__range=[date_from_object, date_to_object]).filter(user_asked__in=users_ids)
            info_string = f"Stats for {teacher}'s class from {uk_date_from_str} to {uk_date_to_str}"
        if data_type=='individual student':
            info_string = f"Stats for {student} from {uk_date_from_str} to {uk_date_to_str}"
            user_asked = User.objects.get(username = student)
            attempts = Attempt.objects.filter(user_asked=user_asked).filter(date_created__date__range=[date_from_object, date_to_object])
            #put in code that creates heatmaps and graph here
        if not attempts:
            return render(request, 'error.html',{'error':'Student has not used app enough yet'})
        df = pd.DataFrame.from_records(attempts.values())
        print('df')
        print(df)
        x_list = [obj.x for obj in attempts]
        df['x'] = x_list
        y_list = [obj.y for obj in attempts]
        df['y'] = y_list
        df_cleaned = df.dropna(subset=['correct'])
        percentage_correct = df_cleaned.groupby(['x', 'y'])['correct'].mean()
        percentage_correct = percentage_correct.reset_index()

        # Create a pivot table
        pivot_table = pd.pivot_table(percentage_correct, values='correct', index='y', columns='x')

        # Display the pivot table
        #plt.figure(figsize=(10, 8))
        plt.figure(figsize=(7, 7))
        norm = plt.Normalize(vmin=0, vmax=1)
        sns.heatmap(pivot_table, annot=True, fmt=".0%", cmap="RdYlGn",norm=norm, cbar=False)
        
        
        plt.title('Percentage correct heatmap')
        plt.xlabel('')
        plt.ylabel('')
        #invert y axis
        ax = plt.gca()
        ax.invert_yaxis()
        # Save the heatmap to a temporary file or buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        with Image.open(img_buffer) as img:
            img = img.convert('RGB')  # Convert image to RGB mode if needed

            # Get image dimensions
            width, height = img.size

            # Initialize crop boundaries
            left, top, right, bottom = width, height, 0, 0

            # Scan image to find boundaries
            for x in range(width):
                for y in range(height):
                    if img.getpixel((x, y)) != (255, 255, 255):  # Check for non-white pixels (white is (255, 255, 255))
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)

            # Crop the image using identified boundaries
            cropped_img = img.crop((left - 10, top - 10, right + 10, bottom + 35))

            # Save the cropped image back to the buffer
            cropped_img_buffer = BytesIO()
            cropped_img.save(cropped_img_buffer, format='png')
            cropped_img_buffer.seek(0)
            img_str = base64.b64encode(cropped_img_buffer.read()).decode('utf-8')

        # Close the buffers
        img_buffer.close()
        cropped_img_buffer.close()

        

        df_time = df.dropna(subset=['time_taken'])
        average_time = df_time.groupby(['x', 'y'])['time_taken'].mean()/1000
        average_time = average_time.reset_index()

        pivot_table_average_time = pd.pivot_table(average_time, values='time_taken', index='y', columns='x')
        #plt.figure(figsize=(10, 8))
        plt.figure(figsize=(7, 7))
        norm = plt.Normalize(vmin=0, vmax=6.2)
        sns.heatmap(pivot_table_average_time, annot=True, fmt=".1f", cmap="RdYlGn_r",norm=norm, cbar=False)
        plt.title('Average time of correct answers heatmap')
        plt.xlabel('')
        plt.ylabel('')
        #invert y axis
        ax = plt.gca()
        ax.invert_yaxis()
        img_buffer2 = BytesIO()
        plt.savefig(img_buffer2, format='png')
        img_buffer2.seek(0)


        with Image.open(img_buffer2) as img:
            img = img.convert('RGB')  # Convert image to RGB mode if needed

            # Get image dimensions
            width, height = img.size

            # Initialize crop boundaries
            left, top, right, bottom = width, height, 0, 0

            # Scan image to find boundaries
            for x in range(width):
                for y in range(height):
                    if img.getpixel((x, y)) != (255, 255, 255):  # Check for non-white pixels (white is (255, 255, 255))
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)

            # Crop the image using identified boundaries
            cropped_img = img.crop((left - 10, top - 10, right + 10, bottom + 35))

            # Save the cropped image back to the buffer
            cropped_img_buffer = BytesIO()
            cropped_img.save(cropped_img_buffer, format='png')
            cropped_img_buffer.seek(0)
            img_str2 = base64.b64encode(cropped_img_buffer.read()).decode('utf-8')

        # Close the buffers
        img_buffer2.close()
        cropped_img_buffer.close()

        #get the effort charts here
        if data_type=='individual student':
            user_asked = User.objects.get(username = student)
            attempts = Attempt.objects.filter(user_asked=user_asked).filter(date_created__date__range=[date_from_object, date_to_object])
            effort_df = pd.DataFrame.from_records(attempts.values())
            total_attempts = len(effort_df)
            print(effort_df)
            effort_df['date_created'] = pd.to_datetime(df['date_created'])

            # Extract the day from the 'date_created' column
            effort_df['day'] = effort_df['date_created'].dt.date

            # Group by 'day' and count the number of rows for each day
            
            grouped_by_day = effort_df.groupby('day').size().reset_index(name='count')
            
            print(grouped_by_day)
            plt.figure(figsize=(6, 6))
            sns.barplot(x='day', y='count', data=grouped_by_day,color=(255/255, 255/255, 120/255))
            plt.title(f'{total_attempts} questions grouped by day.')
            plt.xlabel('Day')
            plt.ylabel('Attempts')
            
            
            img_buffer3 = BytesIO()
            plt.savefig(img_buffer3, format='png')
            img_buffer3.seek(0)
            img_str3 = base64.b64encode(img_buffer3.read()).decode('utf-8')

            grouped_by_correct = effort_df.groupby('correct').size().reset_index(name='count').replace({True: 'Correct', False: 'Incorrect'})
            print(grouped_by_correct)
            plt.figure(figsize=(6, 6))
            colours = [(255/255, 185/255, 147/255), (177/255, 222/255, 113/255)]
            sns.barplot(x='correct', y='count', hue='correct', data=grouped_by_correct, palette=colours, legend=False)
            plt.title(f'{total_attempts} questions grouped by correctness.')
            plt.xlabel('Correct')
            plt.ylabel('Attempts')
            img_buffer4 = BytesIO()
            plt.savefig(img_buffer4, format='png')
            img_buffer4.seek(0)
            img_str4 = base64.b64encode(img_buffer4.read()).decode('utf-8')
            admin = Admin.objects.get(user=request.user.id)
            teachers = Teacher.objects.filter(admin=admin)
            students = Student.objects.filter(admin=admin)
            context = {'students':students,'teachers':teachers,'heatmap_image': img_str,'heatmap_image2': img_str2,'student':student,'info_string':info_string,'heatmap_image3':img_str3,'heatmap_image4':img_str4}
        if data_type=='whole class':
            attempts = Attempt.objects.filter(date_created__date__range=[date_from_object, date_to_object]).filter(user_asked__in=users_ids)
            effort_df = pd.DataFrame.from_records(attempts.values())
            print(effort_df)
            grouped_by_user = effort_df.groupby('user_asked_id').size().reset_index(name='count')
            grouped_by_user['name'] = grouped_by_user['user_asked_id'].apply(lambda x: User.objects.get(id=x).username)
            grouped_by_user = grouped_by_user.sort_values(by='count', ascending=False)
            plt.figure(figsize=(14, 6))
            # Create bar plot
            ax = sns.barplot(x='count', y='name', data=grouped_by_user, color=(255/255, 255/255, 120/255))
            ax.set_yticklabels([f"{name} ({count} attempts)" for name, count in zip(grouped_by_user['name'], grouped_by_user['count'])])
            # Modify x-axis labels to include count
            
            plt.title('Questions attempted for each student')
            plt.xlabel('Attempts')
            plt.ylabel('Students')
            img_buffer5 = BytesIO()
            plt.savefig(img_buffer5, format='png')
            img_buffer5.seek(0)
            img_str5 = base64.b64encode(img_buffer5.read()).decode('utf-8')
            admin = Admin.objects.get(user=request.user.id)
            teachers = Teacher.objects.filter(admin=admin)
            students = Student.objects.filter(admin=admin)
            context = {'students':students,'teachers':teachers,'heatmap_image': img_str,'heatmap_image2': img_str2,'student':student,'info_string':info_string,'heatmap_image5': img_str5}
        # Pass the base64-encoded image string to the template
        return render(request, 'admin_stats.html',context)
        
        
    
