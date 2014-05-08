from classy import Class
from classy import CosmoSevereError
import itertools
import sys
import numpy as np
import unittest
from nose_parameterized import parameterized

def powerset(iterable):
    xs = list(iterable)
    # note we return an iterator rather than a list
    return itertools.chain.from_iterable(
        itertools.combinations(xs,n) for n in range(1, len(xs)+1))

class TestClass(unittest.TestCase):
    """
    Testing Class and its wrapper classy on different cosmologies

    To run it, do
    ~] nosetest test_class.py

    It will run many times Class, on different cosmological scenarios, and
    everytime testing for different output possibilities (none asked, only mPk,
    etc..)

    """

    def setUp(self):
        """
        set up data used in the tests.
        setUp is called before each test function execution.
        """
        self.cosmo = Class()

        self.verbose = {
            'input_verbose': 1,
            'background_verbose': 1,
            'thermodynamics_verbose': 1,
            'perturbations_verbose': 1,
            'transfer_verbose': 1,
            'primordial_verbose': 1,
            'spectra_verbose': 1,
            'nonlinear_verbose': 1,
            'lensing_verbose': 1,
            'output_verbose': 1}
        self.scenario = {'lensing':'yes'}

    def tearDown(self):
        self.cosmo.struct_cleanup()
        self.cosmo.empty()
        del self.scenario

    @parameterized.expand(
        itertools.product(
            ('LCDM',
             'Mnu',
             'Positive_Omega_k',
             'Negative_Omega_k',
             'Isocurvature_modes', ),
            ({'output': ''}, {'output': 'mPk'}, {'output': 'tCl'},
             {'output': 'tCl pCl lCl'}, {'output': 'mPk tCl lCl', 'P_k_max_h/Mpc':10},
             {'output': 'nCl sCl'}, {'output': 'tCl pCl lCl nCl sCl'}),
            ({'gauge': 'newtonian'}, {'gauge': 'sync'}),
            ({}, {'non linear': 'halofit'})))
    def test_wrapper_implementation(self, name, scenario, gauge, nonlinear):
        """Create a few instances based on different cosmologies"""
        if name == 'Mnu':
            self.scenario.update({'N_ncdm': 1, 'm_ncdm': 0.06})
        elif name == 'Positive_Omega_k':
            self.scenario.update({'Omega_k': 0.01})
        elif name == 'Negative_Omega_k':
            self.scenario.update({'Omega_k': -0.01})
        elif name == 'Isocurvature_modes':
            self.scenario.update({'ic': 'ad,nid,cdi', 'c_ad_cdi': -0.5})

        self.scenario.update(scenario)
        if scenario != {}:
            self.scenario.update(gauge)
        self.scenario.update(nonlinear)

        sys.stderr.write('\n\n---------------------------------\n')
        sys.stderr.write('| Test case %s |\n' % name)
        sys.stderr.write('---------------------------------\n')
        for key, value in self.scenario.iteritems():
            sys.stderr.write("%s = %s\n" % (key, value))
        sys.stderr.write("\n")

        setting = self.cosmo.set(
            dict(self.verbose.items()+self.scenario.items()))
        self.assertTrue(setting, "Class failed to initialize with input dict")

        cl_list = ['tCl', 'lCl', 'pCl', 'nCl', 'sCl']

        # Depending on the cases, the compute should fail or not
        should_fail = True
        output = self.scenario['output'].split()
        for elem in output:
            if elem in ['tCl', 'pCl']:
                for elem2 in output:
                    if elem2 == 'lCl':
                        should_fail = False
                        break

        if not should_fail:
            self.cosmo.compute()
        else:
            self.assertRaises(CosmoSevereError, self.cosmo.compute)
            return

        self.assertTrue(
            self.cosmo.state,
            "Class failed to go through all __init__ methods")
        if self.cosmo.state:
            print '--> Class is ready'
        # Depending
        if 'output' in self.scenario.keys():
            # Positive tests
            output = self.scenario['output']
            for elem in output.split():
                if elem in cl_list:
                    print '--> testing raw_cl function'
                    cl = self.cosmo.raw_cl(100)
                    self.assertIsNotNone(cl, "raw_cl returned nothing")
                    self.assertEqual(
                        np.shape(cl['tt'])[0], 101,
                        "raw_cl returned wrong size")
                if elem == 'mPk':
                    print '--> testing pk function'
                    pk = self.cosmo.pk(0.1, 0)
                    self.assertIsNotNone(pk, "pk returned nothing")
            # Negative tests of output functions
            if not any([elem in cl_list for elem in output.split()]):
                print '--> testing absence of any Cl'
                self.assertRaises(CosmoSevereError, self.cosmo.raw_cl, 100)
            if 'mPk' not in self.scenario['output'].split():
                print '--> testing absence of mPk'
                #args = (0.1, 0)
                self.assertRaises(CosmoSevereError, self.cosmo.pk, 0.1, 0)

    @parameterized.expand(
        itertools.product(
            ('massless', 'massive', 'both'),
            ('photons', 'massless', 'exact'),
            ('t', 's, t')))
    def test_tensors(self, scenario, method, modes):
        """Test the new tensor mode implementation"""
        self.scenario = {}
        if scenario == 'massless':
            self.scenario.update({'N_eff': 3.046, 'N_ncdm':0})
        elif scenario == 'massiv':
            self.scenario.update(
                {'N_eff': 0, 'N_ncdm': 2, 'm_ncdm': '0.03, 0.04',
                 'deg_ncdm': '2, 1'})
        elif scenario == 'both':
            self.scenario.update(
                {'N_eff': 1.5, 'N_ncdm': 2, 'm_ncdm': '0.03, 0.04',
                 'deg_ncdm': '1, 0.5'})

        sys.stderr.write('\n\n---------------------------------\n')
        sys.stderr.write('| Test case: %s %s %s |\n' % (
            scenario, method, modes))
        sys.stderr.write('---------------------------------\n')
        self.scenario.update({
            'tensor method': method, 'modes': modes,
            'output': 'tCl, pCl'})
        for key, value in self.scenario.iteritems():
            sys.stderr.write("%s = %s\n" % (key, value))
        sys.stderr.write("\n")
        self.cosmo.set(
            dict(self.verbose.items()+self.scenario.items()))
        self.cosmo.compute()

    @parameterized.expand(
        itertools.izip(
            powerset(['100*theta_s', 'Omega_dcdm']),
            powerset([1.04, 0.20]),))
    def test_shooting_method(self, variables, values):
        Omega_cdm = 0.25

        scenario = {'Omega_b': 0.05, }

        for variable, value in zip(variables, values):
            scenario.update({variable: value})

        if 'Omega_dcdm' in variables:
            scenario.update({
                'Gamma_dcdm': 100,
                'Omega_cdm': Omega_cdm-scenario['Omega_dcdm']})
        else:
            scenario.update({
                'Omega_cdm': Omega_cdm})

        sys.stderr.write('\n\n---------------------------------\n')
        sys.stderr.write('| Test shooting: %s |\n' % (
            ', '.join(variables)))
        sys.stderr.write('---------------------------------\n')
        for key, value in scenario.iteritems():
            sys.stderr.write("%s = %s\n" % (key, value))
        sys.stderr.write("\n")

        scenario.update(self.verbose)
        self.assertTrue(
            self.cosmo.set(scenario),
            "Class failed to initialise with this input")
        self.assertRaises
        self.cosmo.compute()

        # Now, check that the values are properly extracted
        for variable, value in zip(variables, values):
            if variable == '100*theta_s':
                computed_value = self.cosmo.get_current_derived_parameters(
                    [variable])[variable]
                self.assertAlmostEqual(
                    value, computed_value, places=5)


if __name__ == '__main__':
    unittest.main()
