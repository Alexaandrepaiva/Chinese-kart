from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from direct.interval.IntervalGlobal import Sequence, LerpScaleInterval, Func, Wait

class StartCountdown:
    def __init__(self, base, on_finish=None):
        self.base = base
        self.on_finish = on_finish
        self.text = OnscreenText(
            text='', pos=(0, 0.2), scale=0.2, fg=(1, 1, 0.5, 1), bg=(0,0,0,0),
            align=TextNode.ACenter, mayChange=True, parent=self.base.aspect2d, shadow=(0,0,0,0.7), font=None
        )
        self.text.hide()
        self.sequence = None

    def show_countdown(self):
        self.text.setScale(0.5)
        self.text.show()
        self._play_sequence()

    def _play_sequence(self):
        steps = [
            ("3", (1, 0.5, 0.5, 1)),
            ("2", (1, 1, 0.5, 1)),
            ("1", (0.5, 1, 0.5, 1)),
            ("RUN", (0.5, 1, 0.5, 1)),
        ]
        seq = []
        for i, (txt, color) in enumerate(steps):
            seq.append(Func(self._set_text, txt, color))
            seq.append(Func(self._bounce_anim))
            seq.append(Wait(1.0 if txt != "RUN" else 0.8))
        seq.append(Func(self.text.hide))
        if self.on_finish:
            seq.append(Func(self.on_finish))
        self.sequence = Sequence(*seq)
        self.sequence.start()

    def _set_text(self, txt, color):
        self.text.setText(txt)
        self.text.setFg(color)
        self.text.setScale(0.5)
        self.text.setZ(0.2)

    def _bounce_anim(self):
        # Animate scale and position for bounce effect
        bounce = Sequence(
            LerpScaleInterval(self.text, 0.2, 1.0, startScale=0.5),
            LerpScaleInterval(self.text, 0.1, 0.75, startScale=1.0),
            LerpScaleInterval(self.text, 0.1, 1.0, startScale=0.75),
        )
        bounce.start()

    def cleanup(self):
        if self.sequence:
            self.sequence.finish()
        self.text.destroy()
