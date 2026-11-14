"""Physical, compiled adversarial mutants of PR70's original compare() code.

Ten distinct source rewrites; actual observer is not modified. The oracle is
independent: expected source outcomes are specified for each discriminating
fixture, rather than copied from the mutated implementation.
"""
from __future__ import annotations
from pathlib import Path
import tempfile
import types
import unittest
from tools import verify_operational_equivalence as original

SOURCE=Path(original.__file__).read_text(encoding='utf-8')


def obs(*,code=0,stdout=b'OK\n',stderr=b''):
    return {'exit_code':code,'stdout':stdout,'stderr':stderr}


def mutation(name:str,old:str,new:str):
    if SOURCE.count(old)!=1:
        raise RuntimeError(f'non-unique original source mutation {name}')
    altered=SOURCE.replace(old,new)
    with tempfile.TemporaryDirectory(prefix='hforge-op-mutant-') as tmp:
        path=Path(tmp)/'mutant.py';path.write_text(altered,encoding='utf-8')
        raw=path.read_bytes()
        if raw==SOURCE.encode():raise RuntimeError('mutant not physically applied')
        code=compile(raw,str(path),'exec')
        module=types.ModuleType('mutant_'+name)
        module.__file__=str(path)
        exec(code,module.__dict__)
        yield module


class ActualPR70SourceFalsifiers(unittest.TestCase):
    def test_ten_real_physical_mutants_refuted(self):
        cases=[
          ('stdout_equality_deleted','left["stdout"] == right["stdout"]','True',
            [obs()], [obs(stdout=b'CHANGED\n')], 'REFUTED'),
          ('exit_zero_deleted','left["exit_code"] == right["exit_code"] == 0',
            'left["exit_code"] == right["exit_code"]',
            [obs(code=4)], [obs(code=4)], 'REFUTED'),
          ('nonempty_stdout_deleted','bool(left["stdout"]) and bool(right["stdout"])',
            'True', [obs(stdout=b'')], [obs(stdout=b'')], 'REFUTED'),
          ('missing_reported_failure','if not passed:', 'if False:',
            [obs()], [obs(stdout=b'MUTATED')], 'REFUTED'),
          ('failure_count_overridden','"passed": len(cases) - len(failures)',
            '"passed": len(cases)',
            [obs()], [obs(stdout=b'X')], 'REFUTED'),
          ('false_all_pass_status','if not failures else "REFUTED_FINITE_OBSERVATIONS"',
            'if True else "REFUTED_FINITE_OBSERVATIONS"',
            [obs()], [obs(stdout=b'X')], 'REFUTED'),
          ('stderr_nonempty_policy_deleted','not left["stderr"] and not right["stderr"]', 'True',
            [obs(stderr=b'warning')], [obs(stderr=b'warning')], 'REFUTED'),
          ('left_stdout_wrong_type','not isinstance(obs["stdout"], bytes)', 'False',
            [{'exit_code':0,'stdout':'not bytes','stderr':b''}],
            [{'exit_code':0,'stdout':'not bytes','stderr':b''}], 'ValueError'),
          ('duplicate_denominator_accepted','len(cases) != len(set(cases))','False',
            [obs()], [obs()], 'duplicate'),
          ('boolean_exit_code_accepted','type(obs["exit_code"]) is not int','False',
            [obs(code=True)], [obs(code=True)], 'ValueError'),
        ]
        killed=0
        for name,old,new,left,right,oracle in cases:
            with self.subTest(mutant=name):
                key='x'; names=[key,key] if oracle=='duplicate' else [key]
                before={key:left[0]};after={key:right[0]}
                if oracle in ('ValueError','duplicate'):
                    with self.assertRaises(ValueError):
                        original.compare(names,before,after)
                else:
                    self.assertEqual(original.compare(names,before,after)['status'],
                                     'REFUTED_FINITE_OBSERVATIONS')
                for m in mutation(name,old,new):
                    mutant_violates_oracle=False
                    try:
                        got=m.compare(names,before,after)
                    except Exception as exc:
                        # Canonical comparator requires a specific ValueError
                        # for malformed inputs. A TypeError is a changed
                        # error-contract outcome, NOT a product PASS.
                        mutant_violates_oracle=(oracle=='ValueError'
                            and type(exc) is not ValueError)
                        if not mutant_violates_oracle:
                            self.fail(f'undiscriminated mutant {name}: {exc!r}')
                    else:
                        if oracle in ('ValueError','duplicate'):
                            mutant_violates_oracle=True
                        else:
                            mutant_violates_oracle=(got!=original.compare(
                                names,before,after))
                    self.assertTrue(mutant_violates_oracle,
                                    'real physical source mutation survived oracle')
                    killed+=1
        self.assertEqual(killed,10)


if __name__=='__main__':unittest.main()
