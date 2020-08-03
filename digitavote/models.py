from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from .utils.security import (
    generate_sign_token,
    validate_sign_token,
    generate_token,
    generate_secure_filename,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)
from sqlalchemy import MetaData
from datetime import datetime


convention = {
"ix": 'ix_%(column_0_label)s',
"uq": "uq_%(table_name)s_%(column_0_name)s",
"ck": "ck_%(table_name)s_%(column_0_name)s",
"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
"pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)


class Voters(UserMixin, db.Model):
    __tablename__ ="voters"
    id = db.Column(db.Integer, primary_key=True)
    id_number = db.Column(db.String(50), unique=True, 
                                        index=True, 
                                        nullable=False
                                        )
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, index=True)
    level = db.Column(db.String(30), nullable=False, default="level")
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200))
    dp_fname = db.Column(db.String(180))
    
    otp = db.relationship("OTPs", backref="voter", uselist=False)
    vrn = db.relationship("VRNs", backref="voter", uselist=False)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, pass_):
        self.password_hash = generate_password_hash(pass_)

    def verify_password(self, pass_):
        return check_password_hash(self.password_hash, pass_)
    
    def create_dp_name(self):
        self.dp_name = self.id_number.lower() + "_" + generate_secure_filename(generate_token(self.id_number, length=15)).lower()
    
    def get_dp_name(self):
        return self.dp_name

    def has_vrn(self):
        return True if self.vrn else False
    
    def create_vrn(self):
        vrn = "VRN-"
        vrn += f"{generate_token(generate_token(self.full_name), length=5)}-"
        vrn += f"{generate_token(self.id_number, length=10)}-"
        vrn += f"{generate_token(generate_token(self.id_number), length=5)}".upper()
        voter_vrn = VRNs(vrn=vrn, voter=self)
        db.session.add(self)
        db.session.commit()
    
    def get_vrn(self):
        return self.vrn.vrn
    
    def valid_id_number(self, id):
        id_n = Voters.query.filter_by(id_number=id).first()
        return True if id_n else False
    
    def get_sms_otp(self):
        return self.otp.otp[:6]
    
    def valid_otp(self, otp):
        return True if self.get_sms_otp() == otp else False
    
    def has_otp(self):
        otp = self.otp
        return True if otp else False
    
    def otp_expired(self, age):
        if not self.has_otp():
            return True

        good = validate_sign_token(self.otp.otp, max_age=age)

        return False if good else True 

    def add_otp(self, type_=None):

        key = generate_token(self.id_number)
        new_otp, ts = generate_sign_token(key)
        
        if not type_:
            voter_otp = OTPs(otp=new_otp, time_generated=ts, voter=self)
        else:
            self.otp.otp = new_otp
            self.otp.time_generated = ts
        
        db.session.add(self)
        db.session.commit()
        print(self.get_sms_otp())
        
    def __repr__(self):
        return f'Voter<{self.id_number}, {self.full_name}>'

class OTPs(db.Model):
    __tablename__ =  "otps"
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey("voters.id", onupdate="CASCADE"))
    otp = db.Column(db.String(128), nullable=False)
    time_generated = db.Column(db.String(100))
    def __repr__(self):
        return f'OTP<{self.otp}, {self.voter_id}>'

class VRNs(db.Model):
    __tablename__ =  "vrns"
    id = db.Column(db.Integer, primary_key=True)
    vrn = db.Column(db.String(120), index=True, unique=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voters.id'))


    def __repr__(self):
        return f'VRN<{self.vrn}, {self.voter_id}>'



class Posts(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    post_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))
    level = db.Column(db.String(30), nullable=False)
    payment = db.Column(db.Integer, default=0, nullable=False)


    def __repr__(self):
        return f"Posts<{self.post_name}, {self.payment}>"

class Candidates(UserMixin, db.Model):
    __tablename__ = "candidates"
    id = db.Column(db.Integer, primary_key=True)
    id_number = db.Column(db.String(50), 
                            db.ForeignKey("voters.id_number", onupdate="CASCADE", ondelete="CASCADE"), 
                            index=True,
                            unique=True)
    password_hash = db.Column(db.String(180))
    registered = db.Column(db.Boolean, default=False, nullable=False)
    post_apply = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)
    agenda = db.Column(db.String(250))
    nick_name = db.Column(db.String(100))
    tag_name = db.Column(db.String(60))
    
    user_data = db.relationship("Voters", backref=db.backref("candidate", uselist=False))
    payment = db.relationship("Payments", backref="candidate", uselist=False)
    post = db.relationship("Posts", backref="candidate", uselist=False)
    
    @property
    def password(self):
        raise AttributeError("You can access this property")

    @password.setter
    def password(self, pass_):
        self.password_hash = generate_password_hash(pass_)

    def verify_password(self, pass_):
        return check_password_hash(self.password_hash, pass_)
    
    def __repr__(self):
        return f"Candidates<{self.user_data.full_name}, {self.registered}, {self.post.post_name}>"

class Payments(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    ref_number = db.Column(db.String(100), nullable=False, unique=True)
    payment_by = db.Column(db.Integer, db.ForeignKey("candidates.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Integer, nullable=False, default=0)
    paid = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"Payments<{self.ref_number}, {self.amount}, {self.paid}>"

class Admins(UserMixin, db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(180))
    full_name = db.Column(db.String(100), default='Admin', nullable=True)
    phone = db.Column(db.String(20))
    dp_fname = db.Column(db.String(180))
    super_mod = db.Column(db.Boolean, default=False, nullable=False)

    @classmethod
    def create_admin(cls, email, full_name="Admin", super_mod=False):
        new_admin = cls(email=email, full_name=full_name, super_mod=super_mod)
        return new_admin
    
    @property
    def password(self):
        raise AttributeError("You can access this property")

    @password.setter
    def password(self, pass_):
        self.password_hash = generate_password_hash(pass_)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"Admin<{self.email}, {self.super_mod}>"

class GenPassword(db.Model):
    __tablename__ = "gen_passkeys"
    id = db.Column(db.Integer, primary_key=True )
    id_number = db.Column(db.String(50), 
                            db.ForeignKey("voters.id_number", onupdate="CASCADE", ondelete="CASCADE"), 
                            index=True,
                            unique=True)
    password_hash = db.Column(db.String(180))

    voter = db.relationship("Voters", backref=db.backref("gen_pass", uselist=False))

    @property
    def password(self):
        raise AttributeError("You can access this property")

    @password.setter
    def password(self, pass_):
        self.password_hash = generate_password_hash(pass_)

    def verify_password(self, pass_):
        return check_password_hash(self.password_hash, pass_)
    
    def __repr__(self):
        return f"GenPasswasord<{self.id}, {self.voter.full_name}>"


class Preferences(db.Model):
    __tablename__ = "preferences"
    id = db.Column(db.Integer, primary_key=True)
    voting_start = db.Column(db.String(40))
    voting_end = db.Column(db.String(40))
    reg_start = db.Column(db.String(40))
    reg_end = db.Column(db.String(40))

class Votes(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    vote_ref = db.Column(db.Integer, db.ForeignKey("vrns.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    vote_by = db.Column(db.String(50), db.ForeignKey("voters.id_number", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    vote_for = db.Column(db.String(50), db.ForeignKey("candidates.id_number", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    vote_post = db.Column(db.Integer, db.ForeignKey("posts.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)


    vrn = db.relationship("VRNs", backref = db.backref("votes", lazy='dynamic'))
    voter = db.relationship("Voters", backref = db.backref("votes", lazy='dynamic'))
    candidate = db.relationship("Candidates", backref = db.backref("votes", lazy='dynamic'))
    post = db.relationship("Posts", backref = db.backref("votes", lazy='dynamic'))

    def __repr__(self):
        return f"Vote<ID:{self.id}, BY:{self.vote_by}, FOR:{self.vote_for}, POST:{self.vote_post}>"