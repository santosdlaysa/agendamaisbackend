from src.config.database import db
from datetime import datetime, time


class WorkingHours(db.Model):
    """Horários de trabalho do profissional por dia da semana"""
    __tablename__ = 'working_hours'

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Segunda, 1=Terça, ..., 6=Domingo
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    break_start = db.Column(db.Time, nullable=True)  # Início do intervalo (ex: almoço)
    break_end = db.Column(db.Time, nullable=True)  # Fim do intervalo
    is_available = db.Column(db.Boolean, default=True)  # Se trabalha neste dia
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento
    professional = db.relationship('Professional', backref=db.backref('working_hours', lazy=True))

    # Índice para buscas rápidas
    __table_args__ = (
        db.UniqueConstraint('professional_id', 'day_of_week', name='unique_professional_day'),
    )

    DAY_NAMES = {
        0: 'Segunda-feira',
        1: 'Terça-feira',
        2: 'Quarta-feira',
        3: 'Quinta-feira',
        4: 'Sexta-feira',
        5: 'Sábado',
        6: 'Domingo'
    }

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'professional_id': self.professional_id,
            'day_of_week': self.day_of_week,
            'day_name': self.DAY_NAMES.get(self.day_of_week, ''),
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'break_start': self.break_start.strftime('%H:%M') if self.break_start else None,
            'break_end': self.break_end.strftime('%H:%M') if self.break_end else None,
            'is_available': self.is_available
        }

    @staticmethod
    def get_professional_schedule(professional_id):
        """Retorna agenda completa do profissional"""
        hours = WorkingHours.query.filter_by(professional_id=professional_id).all()
        schedule = {}
        for h in hours:
            schedule[h.day_of_week] = h.to_dict()
        return schedule

    @staticmethod
    def is_professional_available(professional_id, day_of_week, check_time):
        """Verifica se o profissional está disponível em determinado horário"""
        wh = WorkingHours.query.filter_by(
            professional_id=professional_id,
            day_of_week=day_of_week,
            is_available=True
        ).first()

        if not wh:
            return False

        # Verifica se está dentro do horário de trabalho
        if check_time < wh.start_time or check_time >= wh.end_time:
            return False

        # Verifica se está no intervalo
        if wh.break_start and wh.break_end:
            if wh.break_start <= check_time < wh.break_end:
                return False

        return True

    @staticmethod
    def create_default_schedule(professional_id):
        """Cria horários padrão para um profissional (Segunda a Sexta, 08:00-18:00)"""
        default_hours = []
        for day in range(5):  # Segunda a Sexta
            wh = WorkingHours(
                professional_id=professional_id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(18, 0),
                break_start=time(12, 0),
                break_end=time(13, 0),
                is_available=True
            )
            default_hours.append(wh)

        # Sábado com horário reduzido
        wh_saturday = WorkingHours(
            professional_id=professional_id,
            day_of_week=5,
            start_time=time(8, 0),
            end_time=time(12, 0),
            is_available=True
        )
        default_hours.append(wh_saturday)

        # Domingo fechado
        wh_sunday = WorkingHours(
            professional_id=professional_id,
            day_of_week=6,
            start_time=time(0, 0),
            end_time=time(0, 0),
            is_available=False
        )
        default_hours.append(wh_sunday)

        return default_hours


class ProfessionalBlockedDate(db.Model):
    """Datas bloqueadas do profissional (férias, feriados, etc)"""
    __tablename__ = 'professional_blocked_dates'

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    blocked_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento
    professional = db.relationship('Professional', backref=db.backref('blocked_dates', lazy=True))

    # Índice único
    __table_args__ = (
        db.UniqueConstraint('professional_id', 'blocked_date', name='unique_professional_blocked_date'),
    )

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'professional_id': self.professional_id,
            'blocked_date': self.blocked_date.isoformat() if self.blocked_date else None,
            'reason': self.reason
        }

    @staticmethod
    def is_date_blocked(professional_id, date):
        """Verifica se uma data está bloqueada para o profissional"""
        blocked = ProfessionalBlockedDate.query.filter_by(
            professional_id=professional_id,
            blocked_date=date
        ).first()
        return blocked is not None
