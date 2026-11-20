Name:		jcifs-ng
Version:	2.1.10
Release:	1
Summary:	Java SMB2 and SMB3 client
Group:		Development/Java
License:	LGPL-2.1-or-later
URL:		https://github.com/AgNO3/jcifs-ng
# Tag jcifs-ng-2.1.10. No class files or jars.
Source0:	https://github.com/AgNO3/jcifs-ng/archive/refs/tags/jcifs-ng-%{version}.tar.gz#/jcifs-ng-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.slf4j:slf4j-api)
BuildRequires:	mvn(org.bouncycastle:bcprov-jdk18on)
BuildRequires:	mvn(javax.servlet:javax.servlet-api)

%description
eu.agno3.jcifs:jcifs-ng %{version}, a Java SMB2 and SMB3 client.
The classes live in package jcifs, so this jar stays off the
classpath of jcifs 1.3.17. DialectVersion.SMB311 is the newest
dialect this release negotiates.

%prep
%autosetup -n jcifs-ng-jcifs-ng-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main -name '*.java' | sort > sources.list
test "$(wc -l < sources.list)" -eq 399
test -s src/main/java/jcifs/http/ne.css

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP=%{_javadir}/slf4j-api.jar
CP="$CP:%{_javadir}/bcprov-jdk18on.jar"
CP="$CP:%{_javadir}/javax.servlet.jar"
for jar in ${CP//:/ }; do
	test -s "$jar"
done
mkdir -p classes
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
	-cp "$CP" -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 475
javap -v -classpath classes jcifs.DialectVersion | grep -F -q 'major version: 52'
mkdir -p classes/jcifs/http
cp -p src/main/java/jcifs/http/ne.css classes/jcifs/http/
printf 'Manifest-Version: 1.0\nAutomatic-Module-Name: eu.agno3.jcifsng\n\n' > manifest.mf
jar cfm jcifs-ng.jar manifest.mf -C classes .
jar i jcifs-ng.jar
jar tf jcifs-ng.jar | grep -qx 'jcifs/http/ne.css'
jar tf jcifs-ng.jar | grep -F -q 'jcifs/DialectVersion.class'
desc=$(jar --describe-module --file jcifs-ng.jar)
printf '%s\n' "$desc" | grep -F -q 'eu.agno3.jcifsng'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	printf '%s\n' "$desc"
	exit 1
fi

cat > jcifs-ng.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>eu.agno3.jcifs</groupId>
  <artifactId>jcifs-ng</artifactId>
  <version>%{version}</version>
  <name>jcifs-ng</name>
  <description>Java SMB2 and SMB3 client.</description>
  <url>https://github.com/AgNO3/jcifs-ng/</url>
  <licenses>
    <license>
      <name>LGPL-2.1-or-later</name>
      <url>https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>2.0.17</version>
    </dependency>
    <dependency>
      <groupId>org.bouncycastle</groupId>
      <artifactId>bcprov-jdk18on</artifactId>
      <version>1.86</version>
    </dependency>
    <dependency>
      <groupId>javax.servlet</groupId>
      <artifactId>javax.servlet-api</artifactId>
      <version>4.0.1</version>
      <scope>provided</scope>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact jcifs-ng.pom:jcifs-ng.jar \
	--file-name jcifs-ng \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/eu.agno3.jcifs/jcifs-ng.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "jcifs-ng"' "$idx"
test -s %{buildroot}%{_javadir}/jcifs-ng.jar
if [ -e %{buildroot}%{_javadir}/jcifs.jar ]; then
	echo "jcifs-ng must not own jcifs.jar" >&2
	exit 1
fi

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/jcifs-ng.jar
test -s "$JAR"
CP="%{_javadir}/slf4j-api.jar:%{_javadir}/bcprov-jdk18on.jar"
mkdir -p check
cat > check/Smoke.java << 'END'
import jcifs.DialectVersion;

public class Smoke {
	public static void main(String[] args) {
		DialectVersion version = DialectVersion.SMB311;
		if (!version.isSMB2() || !version.atLeast(DialectVersion.SMB210)) {
			throw new AssertionError(version.name());
		}
		System.out.println("jcifs_ng_ok " + version.name() + " " + version.getDialect());
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
	-cp "$JAR:$CP" -d check check/Smoke.java
"$JAVA_HOME/bin/java" -cp "check:$JAR:$CP" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'jcifs_ng_ok SMB311 785' check/out.txt

%files -f .mfiles
%license LICENSE
%doc README.md CHANGELOG.txt
