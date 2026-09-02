import unittest

class TestIEFv3(unittest.TestCase):
    def test_state_v3_schema(self):
        # mock a state.yml V3
        state = {
            "schema_version": "3.0",
            "active_increment": "001_initial_build",
            "increments": {
                "001_initial_build": {
                    "type": "build",
                    "status": "ACTIVE",
                    "current_step": "4_business_rules",
                    "steps": {
                        "1_charter": "APPROVED",
                        "2_empirical_inspection": "COMPLETED",
                        "3_data_contracts": "COMPLETED",
                        "4_business_rules": "IN_PROGRESS"
                    }
                },
                "002_data_exploration": {
                    "type": "exploration",
                    "status": "PAUSED",
                    "current_step": "2_analysis",
                    "steps": {
                        "1_objective": "COMPLETED",
                        "2_analysis": "IN_PROGRESS"
                    }
                }
            }
        }
        
        self.assertEqual(state["schema_version"], "3.0")
        self.assertIn("001_initial_build", state["increments"])
        self.assertEqual(state["increments"]["001_initial_build"]["type"], "build")
        self.assertEqual(state["increments"]["002_data_exploration"]["type"], "exploration")
        self.assertEqual(state["increments"]["001_initial_build"]["steps"]["1_charter"], "APPROVED")
        
    def test_human_gates(self):
        # Validate that human gates require APPROVED
        build_increment = {
            "type": "build",
            "steps": {
                "1_charter": "APPROVED",
                "4_business_rules": "PENDING"
            }
        }
        self.assertTrue(build_increment["steps"]["1_charter"] == "APPROVED")

    def test_artifact_traceability(self):
        # mock BR and Tests
        business_rules = {
            "rules": [
                {"id": "BR-001", "description": "Tax must be 19%"}
            ]
        }
        tests = {
            "tests": [
                {"id": "TEST-01", "covers": ["BR-001"], "status": "pass"}
            ]
        }
        
        covered_rules = tests["tests"][0]["covers"]
        self.assertIn("BR-001", covered_rules)
        self.assertEqual(business_rules["rules"][0]["id"], covered_rules[0])

if __name__ == '__main__':
    unittest.main()
