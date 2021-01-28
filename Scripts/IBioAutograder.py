from Autograder import Autograder


class IBioAutograder(Autograder):
    @property
    def milestone_num(self):
        """We call our labs 'mini-milestones'"""
        return self.LAB_NUM
