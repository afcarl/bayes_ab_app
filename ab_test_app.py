"""
This applet can be viewed directly on a bokeh-server.
See the README.md file in this directory for instructions on running.
"""

import logging

logging.basicConfig(level=logging.DEBUG)

import lib.bayesian_ab as ab
import numpy as np
from scipy.stats import beta

from bokeh.plotting import segment, line, show, figure, rect, multi_line
from bokeh.objects import Plot, ColumnDataSource, Range1d
from bokeh.properties import Instance, String
from bokeh.server.app import bokeh_app
from bokeh.server.utils.plugins import object_page
from bokeh.widgets import HBox, InputWidget, TextInput, VBoxForm, Slider, PreText, VBox


class ABTestApp(HBox):
    extra_generated_classes = [["ABTestApp", "ABTestApp", "VBox"]]
    jsmodel = "VBox"

    inputs = Instance(VBoxForm)
    outputs = Instance(VBox)

    pretext = Instance(PreText)

    installs_A = Instance(TextInput)
    installs_B = Instance(TextInput)
    views_A = Instance(TextInput)
    views_B = Instance(TextInput)
    sensitivity = Instance(InputWidget)
    plot = Instance(Plot)
    source = Instance(ColumnDataSource)

    @classmethod
    def create(cls):
        """
        This function is called once, and is responsible for
        creating all objects (plots, datasources, etc)
        """
        obj = cls()
        obj.pretext = PreText(text="", width=500, height=80)
        obj.inputs = VBoxForm()
        obj.outputs = VBox()

        #inputs
        obj.source = ColumnDataSource(data=dict(xs=[], ys=[]))
        obj.make_inputs()
        # outputs
        obj.make_data()
        obj.make_line_plot()
        obj.make_stats(err=None)
        obj.set_children()

        return obj

    def make_inputs(self):
        self.installs_A = TextInput(
            title='Version A Installs', name='Version A Installs',
            value='200'
        )
        self.installs_B = TextInput(
            title='Version B Installs', name='Version B Installs',
            value='220'
        )
        self.views_A = TextInput(
            title='Version A Views', name='Version A Views',
            value='100000'
        )
        self.views_B = TextInput(
            title='Version B Views', name='Version B Views',
            value='100000'
        )
        self.sensitivity = Slider(
            title='Sensitivity', name='Sensitivity',
            value=.03, start=0, end=.5
        )

    def make_data(self):

        post_A, post_B = self.get_posteriors()
        samps_A = ab.get_samples(post_A)
        samps_B = ab.get_samples(post_B)

        x0 = min([min(samps_A), min(samps_B)])
        x1 = max([max(samps_A), max(samps_B)])
        x_range = np.linspace(x0, x1, 500)

        self.source.data = dict(xs=[x_range, x_range],
                                ys=[post_A.pdf(x_range), post_B.pdf(x_range)])

    def set_children(self):

        self.children = [self.inputs, self.outputs]

        self.inputs.children = [
            self.installs_A,
            self.installs_B,
            self.views_A,
            self.views_B,
            self.sensitivity
        ]

        self.outputs.children = [
            self.pretext,
            self.plot
        ]

    def make_line_plot(self):
        self.plot = multi_line('xs', 'ys',
                               source=self.source,
                               color=['#1F78B4', '#FB9A99'],
                               legend='Version A',
                               title='Likelihood of Install Rates',
                               height=200,
                               width=500
        )

    def setup_events(self):
        super(ABTestApp, self).setup_events()

        if not self.pretext:
            return

        for w in ["installs_A", "installs_B", "views_A", "views_B", "sensitivity"]:
            getattr(self, w).on_change('value', self, 'input_change')

    def input_change(self, obj, attrname, old, new):
        """
        This callback is executed whenever the input form changes. It is
        responsible for updating the plot, or anything else you want.
        The signature is:
        Args:
            obj : the object that changed
            attrname : the attr that changed
            old : old value of attr
            new : new value of attr
        """
        input_errs = self._check_inputs()

        if input_errs:
            self.make_stats(err=input_errs)
        else:
            self.make_data()
            self.make_stats(err=None)
            self.make_line_plot()

        self.set_children()


    def _check_inputs(self):
        output = []
        i_A = np.float(self.installs_A.value)
        i_B = np.float(self.installs_B.value)
        v_A = np.float(self.views_A.value)
        v_B = np.float(self.views_B.value)
        if i_A < 100:
            output.append('Version A installs < 100')
        if i_B < 100:
            output.append('Version B installs < 100')
        if i_A > v_A:
            output.append('Version A has more installs than views')
        if i_B > v_B:
            output.append('Version B has more installs than views')

        return output

    def get_posteriors(self):
        post_A, post_B = ab.calculate_posteriors(np.float(self.installs_A.value),
                                                 np.float(self.installs_B.value),
                                                 np.float(self.views_A.value),
                                                 np.float(self.views_B.value))
        return post_A, post_B

    def make_stats(self, err):

        if not err:

            post_A, post_B = self.get_posteriors()
            samps_A = ab.get_samples(post_A)
            samps_B = ab.get_samples(post_B)

            p_better = ab.get_prob_better(samps_A, samps_B)
            p_X_better = ab.get_prob_X_better(samps_A, samps_B, self.sensitivity.value)
            lift = ab.get_expected_lift(samps_A, samps_B)

            stats_string = " Probability B > A: {0}\
            \n Probability B > A by {1} Percent: {2}\
            \n Expected Percent Difference: {3}" \
                .format(p_better, self.sensitivity.value * 100, p_X_better, lift)

            self.pretext.text = str(stats_string)

        else:
            err.insert(0, ' ')
            self.pretext.text = '\n Input Error: '.join(err)


# The following code adds a "/bokeh/abtest/" url to the bokeh-server. 
# This URL will render this app. 
@bokeh_app.route("/bokeh/abtest/")
@object_page("AB_Test")
def make_object():
    app = ABTestApp.create()
    return app