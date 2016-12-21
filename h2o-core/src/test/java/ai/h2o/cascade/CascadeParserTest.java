package ai.h2o.cascade;

import ai.h2o.cascade.asts.Ast;
import ai.h2o.cascade.asts.AstNum;
import ai.h2o.cascade.asts.AstNumList;
import ai.h2o.cascade.asts.AstStr;
import org.apache.commons.lang.StringUtils;
import org.junit.BeforeClass;
import org.junit.Test;
import water.TestUtil;
import water.util.Log;

import static org.junit.Assert.*;

/**
 * Test suite for {@link CascadeParser}.
 */
@SuppressWarnings("FieldCanBeLocal")
public class CascadeParserTest extends TestUtil {
  // Initializing a session causes the CascadeStandardLibrary to load
  public static CascadeSession session;

  // Error messages
  private final String UNTERM = "Unterminated string";
  private final String BADEXPR = "Illegal Cascade expression";
  private final String INVESC = "Invalid escape sequence ";
  private final String NONHEX = "Escape sequence contains non-hexademical character ";
  private final String ESCSHRT = "Escape sequence too short";
  private final String ENDSTR = "Unexpected end of string";
  private final String EXPNUM = "Expected a number";
  private final String MULTIP = "Invalid number: multiple points";
  private final String BADNUM = "Invalid number";

  @BeforeClass
  public static void setup() {
    stall_till_cloudsize(1);
    session = new CascadeSession("test");
  }


  @Test public void testParseNumber() {
    astNum_ok("1234567890", 1234567890);
    astNum_ok("0.000001", 0.000001);
    astNum_ok("-2e+03", -2000);
    astNum_ok("2.78e-0004", 2.78e-4);
    astNum_ok("3.2e1000", Double.POSITIVE_INFINITY);
    astNum_ok("nan", Double.NaN);
    astNum_ok("NaN", Double.NaN);
    astNum_ok(".33", 0.33);
    astNum_ok("33.", 33);

    parse_err("127.0.0.1", MULTIP, 0, 9);
    parse_err("1e3e7", BADNUM, 0, 5);
    parse_err("--1", BADNUM, 0, 3);
    parse_err("+1", "Invalid syntax", 0, 1);
    parse_err("-2-3", BADNUM, 0, 4);
    parse_err("0xA7", BADEXPR, 1, 1);
    parse_err("-Inf", BADNUM, 0, 1);
    parse_err("4.nan", BADNUM, 0, 5);
  }

  @Test public void testParseString() {
    astStr_ok("'hello'", "hello");
    astStr_ok("\"one two three\"", "one two three");
    astStr_ok("\"  \\\"  \"", "  \"  ");
    astStr_ok("\"\\\\\"", "\\");
    astStr_ok("'test\"omg'", "test\"omg");
    astStr_ok("'sun\nmoon'", "sun\nmoon");
    astStr_ok("'a\\nb'", "a\nb");
    astStr_ok("'\\n\\r\\t\\b\\f\\'\\\"\\\\'", "\n\r\t\b\f\'\"\\");
    astStr_ok("'\\x00\\xa2\\xBC\\xDe\\xFF\\xcb'", "\u0000\u00A2\u00BC\u00DE\u00FF\u00CB");
    astStr_ok("\"\\uABCD\\u0000\\uffff\"", "\uABCD\u0000\uFFFF");
    astStr_ok("\"\\U0001F578\"", new String(Character.toChars(0x1F578)));

    parse_err("\"hello", UNTERM, 0, 6);
    parse_err("\"one\"two\"", BADEXPR, 5, 1);
    parse_err("\"something\'", UNTERM, 0, 11);
    parse_err("'\\+'", INVESC + "\\+", 1, 2);
    parse_err("'\\0'", INVESC + "\\0", 1, 2);
    parse_err("'\\xA'", NONHEX + "'''", 1, 4);
    parse_err("'\\xHI", NONHEX + "'H'", 1, 4);
    parse_err("'\\u123 spam'", NONHEX + "' '", 1, 6);
    parse_err("'\\U'", ESCSHRT, 1, 3);
    parse_err("'\\U1234aBcD'", "Illegal Unicode codepoint 0x1234ABCD", 1, 10);
    parse_err("'\\U1F578'", ESCSHRT, 1, 8);
    parse_err("'\\U+1F578'", ESCSHRT, 1, 9);
    parse_err("'\\u{1F578}'", NONHEX + "'{'", 1, 6);
  }

  @Test public void testParseNumList() {
    astNumList_ok("[]", new double[0]);
    astNumList_ok("[1 2 3]", ard(1, 2, 3));
    astNumList_ok("[1, 2, 3]", ard(1, 2, 3));
    astNumList_ok("[1     , 2\t, 3,4]", ard(1, 2, 3, 4));
    astNumList_ok("[1 2 3 5 10 2]", ard(1, 2, 3, 5, 10, 2));
    astNumList_ok("[000.1 -3 17.003 2e+01 +11.1 1234567890]", ard(0.1, -3, 17.003, 20, 11.1, 1234567890));
    astNumList_ok("[NaN nan 1.e2 .1e2]", ard(Double.NaN, Double.NaN, 100, 10));
    astNumList_ok("[1,\n2,\n3,\n]", ard(1, 2, 3));
    parse_err("[21 11", ENDSTR, 6, 1);
    parse_err("[1 0.00.0]", MULTIP, 3, 6);
    parse_err("[0 1 true false]", EXPNUM, 5, 1);
    parse_err("[#1 #2 #3]", EXPNUM, 1, 1);
    parse_err("[0 1 'hello']", EXPNUM, 5, 1);
    parse_err("[1:3]", EXPNUM, 2, 1);
    parse_err("[, 1, 2, 3]", EXPNUM, 1, 1);
    parse_err("[1 ,, 2]", EXPNUM, 4, 1);
  }


  //--------------------------------------------------------------------------------------------------------------------
  // Helpers
  //--------------------------------------------------------------------------------------------------------------------

  private static void astNum_ok(String expr, double expected) {
    Ast res = parse(expr);
    assertTrue("Unexpected result of type " + res.getClass().getSimpleName(), res instanceof AstNum);
    assertEquals(expected, (res.exec(null)).getNum(), 1e-10);
  }

  private static void astNumList_ok(String expr, double[] expected) {
    Ast res = parse(expr);
    assertTrue(res instanceof AstNumList);
    assertArrayEquals(expected, (res.exec(null)).getNums(), 1e-10);
  }

  private static void astStr_ok(String expr, String expected) {
    Ast res = parse(expr);
    assertTrue(res instanceof AstStr);
    assertEquals(expected, res.str());
  }

  private static void parse_err(String expr, String expectedError, int expectedPos, int expectedLen) {
    try {
      parse(expr);
      fail("Expression " + expr + " expected to fail, however it did not.");
    } catch (Cascade.SyntaxError e) {
      if (!expectedError.isEmpty())
        assertEquals("Wrong error message", expectedError, e.getMessage());
      if (expectedPos != -1)
        assertEquals("Wrong error position", expectedPos, e.location);
      if (expectedLen != -1)
        assertEquals("Wrong error length", expectedLen, e.length);
    }
  }

  private static Ast parse(String expr) {
    try {
      return Cascade.parse(expr);
    } catch (Cascade.SyntaxError e) {
      Log.info("\n" + e.getClass().getSimpleName() + " in expression:");
      Log.info(expr);
      Log.info(StringUtils.repeat(" ", e.location) +
               StringUtils.repeat("^", Math.max(e.length, 1)) +
               " " + e.getMessage() + "\n");
      throw e;
    }
  }
}
