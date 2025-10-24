from constants import domains

class DummyData:
    def __init__(self):
        self.data = {}

    def add_note_id(self):
        self.data["noteId"] = list(range(1, 16))

    def add_participant_id_note(self):
        self.data["participantId_note"] = ["user_1", "user_3", "user_1", "user_2", "user_1",
                                           "user_1", "user_3", "user_1", "user_2", "user_1",
                                           "user_1", "user_2", "user_1", "user_2", "user_1"]

    def add_domain(self):
        self.data["domain"] = domains

    def add_createdAtMillis(self):
        self.data["createdAtMillis"] = [1696137600000 + i*86400000 for i in range(15)]

    def add_summary(self):
        self.data["summary"] = [f"Note about {d}" for d in domains]

    def add_locked_status(self):
        self.data["lockedStatus"] = ["currently rated helpful"] * 5 + ["currently rated somewhat helpful"] *5 + ["currently rated not helpful"] * 5

    def add_timestamp_statusLock(self):
        self.data["timestampMillisOfStatusLock"] = [1696137600000 + i*86400000 + 3600000 for i in range(15)]

    def add_participant_id_rating(self):
        self.data["participantId_rating"] = ["user_2", "user_1", "user_4", "user_1", "user_3",
                                             "user_2", "user_1", "user_4", "user_1", "user_3",
                                             "user_4", "user_1", "user_3", "user_1", "user_3"]

    def add_agree(self):
        self.data["agree"] = [1 if i % 2 == 0 else 0 for i in range(15)]

    def add_disagree(self):
        self.data["disagree"] = [0 if i % 2 == 0 else 1 for i in range(15)]

    def add_helpfulness_level(self):
        self.data["helpfulnessLevel"] = ["helpful", "somewhat helpful", "helpful", "helpful", "not helpful",
                                         "somewhat helpful", "helpful", "not helpful", "helpful", "somewhat helpful",
                                         "helpful", "not helpful", "helpful", "helpful", "helpful"]

    def add_enrollment_state(self):
        self.data["enrollmentState"] = ["enrolled"] * 15

    def get_data_ready(self):
        self.add_note_id()
        self.add_participant_id_note()
        self.add_domain()
        self.add_createdAtMillis()
        self.add_summary()
        self.add_locked_status()
        self.add_timestamp_statusLock()
        self.add_participant_id_rating()
        self.add_agree()
        self.add_disagree()
        self.add_helpfulness_level()
        self.add_enrollment_state()

if __name__ == '__main__':
    k = DummyData()
    k.get_data_ready()
    print(k.data)