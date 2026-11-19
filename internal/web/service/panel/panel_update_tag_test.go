package panel

import "testing"

func TestPanelVersionFromTag(t *testing.T) {
	cases := []struct{ tag, want string }{
		{"v3.12.0-nosponsor", "3.12.0"},
		{"v3.11.0-nosponsor", "3.11.0"},
		{"v4.0.1-nosponsor", "4.0.1"},
		{"v3.9.0", "3.9.0"},
	}
	for _, tc := range cases {
		if got := panelVersionFromTag(tc.tag); got != tc.want {
			t.Errorf("panelVersionFromTag(%q) = %q, want %q", tc.tag, got, tc.want)
		}
	}
}
