from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Question

app = Flask(__name__)
app.secret_key = 'secret_key'

# DB設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 初回起動時に使う（テーブル作成用）
@app.before_first_request
def create_tables():
    db.create_all()

# ====================
# 一般ユーザ向け
# ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_quiz():
    session['current'] = 0
    session['correct'] = 0
    session['question_ids'] = [q.id for q in Question.query.all()]
    return redirect(url_for('question'))

@app.route('/question')
def question():
    ids = session.get('question_ids', [])
    index = session.get('current', 0)
    if index >= len(ids):
        return redirect(url_for('score'))
    q = Question.query.get(ids[index])
    return render_template('question.html', q=q)

@app.route('/answer', methods=['POST'])
def answer():
    selected = request.form['answer'] == 'True'
    index = session['current']
    q_id = session['question_ids'][index]
    q = Question.query.get(q_id)
    result = selected == q.answer
    if result:
        session['correct'] += 1
    session['current'] += 1
    return render_template('result.html', result=result, explanation=q.explanation)

@app.route('/score')
def score():
    correct = session.get('correct', 0)
    total = len(session.get('question_ids', []))
    percentage = int((correct / total) * 100) if total else 0
    return render_template('score.html', correct=correct, total=total, percentage=percentage)

# ====================
# 管理者向け
# ====================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'pass123':
            session['admin'] = True
            return redirect('/manage')
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if not session.get('admin'):
        return redirect('/admin')
    
    if request.method == 'POST':
        question = request.form['question']
        answer = True if request.form['answer'] == 'True' else False
        explanation = request.form['explanation']
        new_q = Question(question=question, answer=answer, explanation=explanation)
        db.session.add(new_q)
        db.session.commit()
        return redirect('/manage')
    
    all_questions = Question.query.all()
    return render_template('manage.html', questions=all_questions)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'):
        return redirect('/admin')
    q = Question.query.get(id)
    db.session.delete(q)
    db.session.commit()
    return redirect('/manage')

if __name__ == '__main__':
    app.run(debug=True)