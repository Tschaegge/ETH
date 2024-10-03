package ch.ethz.rse.integration.tests;
import ch.ethz.rse.Store;


// expected results:
// NON_NEGATIVE UNSAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class NonNegative_Test_Widening {

  public static void m1() {
    Store s = new Store(10, 1000);
    for (int i = -10; i <= 10; i++) {
        s.get_delivery(i);
    }
  }
}
